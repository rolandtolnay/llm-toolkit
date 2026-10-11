#!/usr/bin/env node
// Linear roadmap server: refreshes a roadmap page from Linear through the
// toolkit's linear.py CLI, serves it on localhost, and runs self-heal passes
// with headless Claude Code. Node 22+, no dependencies.
//
// The page commits its curated config and guidance; the Linear snapshot lives in
// a sidecar script next to it, named by the page's roadmap-snapshot tag, which
// projects keep out of version control.
//
//   node roadmap.mjs <page.html>                 refresh, serve, open browser
//   node roadmap.mjs <page.html> --no-open       refresh and serve only
//   node roadmap.mjs <page.html> --refresh-only  refresh the file and exit
//   node roadmap.mjs <page.html> --check         read Linear, validate, write nothing
//   node roadmap.mjs <page.html> --heal <template> [--instruction TEXT]
//                                                run one self-heal pass and exit
//   node roadmap.mjs <page.html> --heal-dry <template>   print the prompt only

import { createHash, randomUUID } from 'node:crypto'
import { spawn, execFile } from 'node:child_process'
import { realpathSync } from 'node:fs'
import { copyFile, mkdir, readdir, readFile, rename, stat, unlink, writeFile } from 'node:fs/promises'
import { createServer } from 'node:http'
import { homedir } from 'node:os'
import { basename, dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { promisify } from 'node:util'
import { Script } from 'node:vm'

const execFileAsync = promisify(execFile)
const here = dirname(fileURLToPath(import.meta.url))

export const MODEL = 'opus'
export const EFFORT = 'medium'
export const HEAL_TEMPLATES = ['integrate-new', 'reconcile-states', 'recheck-guidance', 'custom']
export const KNOWN_STATE_TYPES = new Set(['triage', 'backlog', 'unstarted', 'started', 'completed', 'canceled', 'duplicate'])
export const CLOSED_STATE_TYPES = new Set(['completed', 'canceled', 'duplicate'])
const LIMITS = Object.freeze({ healTimeout: 15 * 60_000, cliTimeout: 60_000, concurrency: 4, eventLog: 400, backups: 5 })

const guidancePattern = /(<script id="roadmap-guidance" type="application\/json">)([\s\S]*?)(<\/script>)/
const configPattern = /(<script id="roadmap-config" type="application\/json">)([\s\S]*?)(<\/script>)/
const snapshotTagPattern = /<script id="roadmap-snapshot" src="([^"]+)"><\/script>/
const snapshotFilePattern = /^[\s\S]*?window\.ROADMAP_SNAPSHOT = ([\s\S]*);\s*$/

// Per-ticket fields written for the reader. They live in the page; everything else on a task is a Linear fact or derived.
export const GUIDANCE_FIELDS = ['title', 'summary', 'detail', 'input', 'workflow', 'gates', 'curated', 'reviewedHash', 'aiGuidance']

export class RoadmapError extends Error {}

// ---------------------------------------------------------------------------
// Page parsing

export function readBlock(html, pattern, label) {
  const match = html.match(pattern)
  if (!match) throw new RoadmapError(`The page has no ${label} block.`)
  try { return JSON.parse(match[2]) }
  catch { throw new RoadmapError(`The ${label} block is not valid JSON.`) }
}

export function readGuidance(html) {
  const guidance = readBlock(html, guidancePattern, 'roadmap-guidance')
  if (!Array.isArray(guidance.tasks)) throw new RoadmapError('The roadmap-guidance block has no tasks array.')
  return guidance
}

export function snapshotPathFor(page, html) {
  const src = html.match(snapshotTagPattern)?.[1]
  if (!src) throw new RoadmapError('The page has no roadmap-snapshot script tag.')
  if (src.startsWith('/') || src.split('/').includes('..') || /^[a-z]+:/i.test(src)) throw new RoadmapError('The roadmap-snapshot src must be a path below the page directory.')
  return join(dirname(page), src)
}

export function parseSnapshotFile(text) {
  const match = text.match(snapshotFilePattern)
  let snapshot
  try { snapshot = JSON.parse(match?.[1]) } catch {}
  if (!Array.isArray(snapshot?.tasks)) throw new RoadmapError('The snapshot file is not a roadmap snapshot. Delete it and refresh.')
  return snapshot
}

export function encodeSnapshotFile(snapshot) {
  return `// Linear snapshot for a roadmap page, written by roadmap.mjs on refresh. Local only: do not edit or commit.\nwindow.ROADMAP_SNAPSHOT = ${encodeJson(snapshot)};\n`
}

// A fresh checkout has no snapshot yet; the first refresh writes it.
export async function readSnapshotFile(path) {
  try { return parseSnapshotFile(await readFile(path, 'utf8')) }
  catch (error) { if (error.code === 'ENOENT') return { tasks: [] }; throw error }
}

// Overlay the page's guidance on the Linear snapshot, the same way the page script does.
export function combine(snapshot, guidance) {
  const notes = new Map(guidance.tasks.map(entry => [entry.id, entry]))
  const tasks = snapshot.tasks.map(task => ({ ...task, ...notes.get(task.id) }))
  const seen = new Set(tasks.map(task => task.id))
  for (const entry of guidance.tasks) if (!seen.has(entry.id)) tasks.push({ ...entry })
  for (const task of tasks) task.reviewRequired = Boolean(task.missing) || (task.sourceHash !== task.reviewedHash && task.sourceHash !== task.aiGuidance?.sourceHash)
  return { ...snapshot, tasks }
}

// What the snapshot file stores: facts for every task, plus placeholder guidance only for tickets the page has none for.
export function factsOnly(snapshot, guidance) {
  const guided = new Set(guidance.tasks.map(entry => entry.id))
  const strip = task => Object.fromEntries(Object.entries(task).filter(([key]) => key !== 'reviewRequired' && !(guided.has(task.id) && GUIDANCE_FIELDS.includes(key))))
  return { ...snapshot, tasks: snapshot.tasks.map(strip) }
}

export async function loadPage(page) {
  const html = await readFile(page, 'utf8')
  const config = readConfig(html), guidance = readGuidance(html)
  const snapshotPath = snapshotPathFor(page, html)
  const stored = await readSnapshotFile(snapshotPath)
  return { html, config, guidance, snapshotPath, stored, snapshot: combine(stored, guidance) }
}

export function readConfig(html) {
  const config = readBlock(html, configPattern, 'roadmap-config')
  if (!Array.isArray(config.phases) || !config.phases.length) throw new RoadmapError('The roadmap-config block needs at least one phase.')
  for (const phase of config.phases) {
    if (!phase.id || !Array.isArray(phase.projects)) throw new RoadmapError(`Phase ${phase.id || '(unnamed)'} needs an id and a projects array.`)
  }
  return config
}

export function encodeJson(value) {
  // A Linear title such as </script> must stay data inside a standalone HTML file.
  return JSON.stringify(value, null, 1).replaceAll('<', '\\u003c').replaceAll('\u2028', '\\u2028').replaceAll('\u2029', '\\u2029')
}

// Syntax-check every inline classic script so a broken self-heal is caught before reload.
export function validatePage(html) {
  readGuidance(html)
  readConfig(html)
  if (!snapshotTagPattern.test(html)) throw new RoadmapError('The page has no roadmap-snapshot script tag.')
  const scripts = [...html.matchAll(/<script(?![^>]*\btype=)[^>]*>([\s\S]*?)<\/script>/g)]
  if (!scripts.length) throw new RoadmapError('The page has no inline script.')
  for (const [, source] of scripts) {
    try { new Script(source) }
    catch (error) { throw new RoadmapError(`The page script has a syntax error: ${error.message}`) }
  }
  if (!/<body[\s>]/.test(html) || !/id="task-list"/.test(html)) throw new RoadmapError('The page lost its body or task list.')
}

// ---------------------------------------------------------------------------
// Project resolution

export async function findProjectRoot(start) {
  let directory = resolve(start)
  while (true) {
    try { await stat(join(directory, '.linear.json')); return directory }
    catch {}
    const parent = dirname(directory)
    if (parent === directory) throw new RoadmapError('No .linear.json found above the page. Run the Linear skill setup in this project first.')
    directory = parent
  }
}

// Match Pi's project-env loader: nearest file per source, later sources win over
// earlier sources and the shell; null unsets; invalid entries are ignored.
export async function resolveApiKey(root, env = process.env, warn = console.warn) {
  let key = env.LINEAR_API_KEY
  for (const source of ['.claude/settings.local.json', '.agents/env.json', '.pi/env.json']) {
    let directory = root
    while (true) {
      let text
      try { text = await readFile(join(directory, source), 'utf8') }
      catch (error) {
        if (error.code === 'ENOENT') {
          const parent = dirname(directory)
          if (parent === directory) break
          directory = parent
          continue
        }
        warn(`Project env: could not read ${source}; ignoring this source.`)
        break
      }
      try {
        const parsed = JSON.parse(text)
        const entries = source === '.claude/settings.local.json' ? (parsed?.env ?? {}) : parsed
        if (!entries || typeof entries !== 'object' || Array.isArray(entries)) throw new Error()
        if (Object.hasOwn(entries, 'LINEAR_API_KEY')) {
          const value = entries.LINEAR_API_KEY
          if (value === null) key = undefined
          else if (['string', 'number', 'boolean'].includes(typeof value)) key = String(value)
          else warn(`Project env: ignored invalid LINEAR_API_KEY in ${source}.`)
        }
      } catch { warn(`Project env: invalid JSON in ${source}; ignoring this source.`) }
      break
    }
  }
  if (key) return key
  throw new RoadmapError('Linear credentials are unavailable. Set LINEAR_API_KEY in .agents/env.json, .pi/env.json, .claude/settings.local.json (env section) or the shell.')
}

export async function findLinearCli(env = process.env) {
  const candidates = [
    env.LINEAR_CLI,
    resolve(here, '../../linear/scripts/linear.py'),
    join(homedir(), '.agents/skills/linear/scripts/linear.py'),
    join(homedir(), '.claude/skills/linear/scripts/linear.py'),
  ].filter(Boolean)
  for (const candidate of candidates) {
    try { await stat(candidate); return candidate }
    catch {}
  }
  throw new RoadmapError('The Linear CLI (linear.py from the toolkit linear skill) was not found. Set LINEAR_CLI to its path.')
}

// ---------------------------------------------------------------------------
// Linear reads through the CLI

export function makeCli({ cli, cwd, apiKey, run = execFileAsync }) {
  return async function linear(args) {
    let stdout
    try {
      ({ stdout } = await run('uv', ['run', cli, ...args], {
        cwd, timeout: LIMITS.cliTimeout, maxBuffer: 16 * 1024 * 1024,
        env: { ...process.env, LINEAR_API_KEY: apiKey, NO_COLOR: '1' },
      }))
    } catch (error) {
      stdout = error.stdout
      if (!stdout) throw new RoadmapError(`The Linear CLI could not run (${error.code || 'spawn failure'}). Is uv installed and the linear skill present?`)
    }
    let parsed
    try { parsed = JSON.parse(stdout) }
    catch { throw new RoadmapError(`The Linear CLI returned something other than JSON for: ${args[0]}.`) }
    if (!parsed.success) {
      const error = parsed.error || {}
      throw new RoadmapError(`Linear ${args[0]} failed: ${error.code || 'ERROR'} ${error.message || ''}`.trim())
    }
    return parsed.result
  }
}

export async function fetchFacts(linear, config, previous, log = () => {}) {
  const statesResult = await linear(['states'])
  const stateTypes = {}
  for (const team of statesResult.teams || []) for (const state of team.states || []) stateTypes[state.name] = state.type
  const projects = [...new Set(config.phases.flatMap(phase => phase.projects))]
  const listed = new Map()
  for (const project of projects) {
    let after = null
    const seen = new Set()
    do {
      const page = await linear(['list', '--project', project, '--limit', '50', ...(after ? ['--after', after] : [])])
      for (const issue of page.issues || []) listed.set(issue.identifier, { ...issue, projectName: project })
      after = page.pageInfo?.hasNextPage ? page.pageInfo.endCursor : null
      if (after && seen.has(after)) throw new RoadmapError(`Linear pagination for ${project} did not finish.`)
      if (after) seen.add(after)
    } while (after)
    log(`Listed ${project}: ${[...listed.values()].filter(i => i.projectName === project).length} tickets.`)
  }
  const milestones = []
  for (const project of projects) {
    const result = await linear(['milestones', project])
    for (const milestone of result.milestones || []) milestones.push({ project, name: milestone.name, targetDate: milestone.targetDate || null, status: milestone.status || null })
  }
  const wanted = new Set([...listed.keys(), ...previous.tasks.filter(task => task.curated).map(task => task.id)])
  const issues = new Map()
  const requested = new Set(wanted)
  const queue = [...wanted]
  const enqueue = id => { if (id && !requested.has(id)) { requested.add(id); queue.push(id) } }
  while (queue.length) {
    const batch = queue.splice(0, LIMITS.concurrency)
    const results = await Promise.all(batch.map(id => linear(['get', id, '-V']).then(result => [id, result], error => [id, error])))
    for (const [id, result] of results) {
      if (result instanceof Error) {
        if (/ISSUE_NOT_FOUND/.test(result.message)) { issues.set(id, null); continue }
        throw result
      }
      issues.set(id, result)
      for (const relation of result.relations || []) if (relation.type === 'blocked-by') enqueue(relation.issue)
      for (const gate of previous.tasks.find(task => task.id === id)?.gates || []) enqueue(gate)
    }
    log(`Fetched ${issues.size} of ${requested.size} tickets.`)
  }
  return { stateTypes, listed, issues, milestones }
}

// ---------------------------------------------------------------------------
// Merge

function identifierNumber(identifier) {
  const match = /^[A-Z][A-Z0-9]*-(\d+)$/.exec(identifier || '')
  return match ? Number(match[1]) : null
}

export function fingerprint(issue, blockedBy, ownerLabel) {
  return createHash('sha256').update(JSON.stringify({
    title: issue.title, description: issue.description || '', project: issue.project?.id || null,
    blockedBy: [...blockedBy].sort(),
    labels: (issue.labels || []).map(label => label.name).sort(),
    owner: Boolean(ownerLabel) && (issue.labels || []).some(label => label.name === ownerLabel),
  })).digest('hex')
}

export function mergeSnapshot(previous, config, facts, now = new Date().toISOString()) {
  const { stateTypes, listed, issues, milestones = [] } = facts
  const oldTasks = new Map(previous.tasks.map(task => [task.id, task]))
  const phaseOf = projectName => config.phases.find(phase => phase.projects.includes(projectName))?.id || 'later'
  const excluded = labels => (config.excludeLabelPrefixes || []).some(prefix => labels.some(label => label.startsWith(prefix)))
  // Curated tickets stay tracked after they leave the projects; anything else is tracked only while Linear lists it.
  const roots = new Set(previous.tasks.filter(task => task.curated && !task.referenceOnly).map(task => task.id))
  for (const [id, issue] of issues) {
    if (!issue) continue
    const labels = (issue.labels || []).map(label => label.name)
    if (listed.has(id) && !excluded(labels)) roots.add(id)
  }
  const tasks = new Map()
  function add(id) {
    if (tasks.has(id)) return
    const old = oldTasks.get(id)
    const issue = issues.get(id)
    if (!issue) {
      tasks.set(id, {
        ...old, id, number: old?.number ?? identifierNumber(id), title: old?.title || id, linearTitle: old?.linearTitle || id,
        summary: old?.summary || 'This ticket was not returned by Linear.', detail: old?.detail || '', input: old?.input || '',
        url: old?.url || null, phase: 'later', projectName: old?.projectName || 'Unavailable',
        state: 'Unavailable', stateType: 'unavailable', missing: true, assignee: null,
        blockedBy: old?.blockedBy || [], gates: old?.gates || [], workflow: old?.workflow || 'review',
        curated: old?.curated ?? false, referenceOnly: !roots.has(id),
      })
    } else {
      const labels = (issue.labels || []).map(label => label.name)
      const blockedBy = (issue.relations || []).filter(relation => relation.type === 'blocked-by' && relation.issue).map(relation => relation.issue)
      const sourceHash = fingerprint(issue, blockedBy, config.ownerLabel)
      const owner = Boolean(config.ownerLabel) && labels.includes(config.ownerLabel)
      const stateType = issue.state?.type || stateTypes[issue.state?.name] || 'unknown'
      const reviewedHash = old?.reviewedHash ?? null
      tasks.set(id, {
        ...old, id, number: identifierNumber(id), title: old?.title || issue.title, linearTitle: issue.title,
        summary: old?.summary || 'New to this roadmap. Read the ticket before choosing a session.',
        detail: old?.detail || 'This ticket has no reviewed plain-language summary yet.',
        input: old?.input || 'Review the requirements and decide whether this needs your input or can go straight to an agent.',
        workflow: old?.workflow || (owner ? 'owner' : 'review'), owner, labels,
        phase: phaseOf(issue.project?.name), projectName: issue.project?.name || 'Unscheduled', projectId: issue.project?.id || null,
        state: issue.state?.name || 'Unknown', stateType, unknownState: !KNOWN_STATE_TYPES.has(stateType),
        assignee: issue.assignee?.name || null, estimate: issue.estimate ?? null, priority: issue.priority ?? null, url: issue.url || null,
        parent: issue.parent?.identifier || null, children: (issue.children || []).map(child => child.identifier),
        truncated: issue.truncated || [], missing: false, referenceOnly: !roots.has(id),
        blockedBy, gates: old?.gates || [], sourceHash, reviewedHash,
        curated: old?.curated ?? false,
      })
    }
    const task = tasks.get(id)
    for (const dependency of [...task.blockedBy, ...task.gates]) add(dependency)
  }
  for (const id of roots) add(id)
  return combine({
    ...previous, checkedAt: now, trackingSince: previous.trackingSince || now, stateTypes, milestones,
    refresh: { ok: true, attemptedAt: now }, tasks: [...tasks.values()],
  }, { tasks: [] })
}

// ---------------------------------------------------------------------------
// File writes

async function atomicWrite(path, text) {
  const temporary = `${path}.${randomUUID()}.tmp`
  try {
    await writeFile(temporary, text, { flag: 'wx' })
    await rename(temporary, path)
  } finally {
    await unlink(temporary).catch(() => {})
  }
}

// A refresh writes only the snapshot file; the page itself changes only through self-heal or by hand.
export async function refreshFile(path, loadFacts, now = new Date().toISOString()) {
  const { config, guidance, snapshotPath, stored, snapshot: previous } = await loadPage(path)
  let next, error
  try {
    next = mergeSnapshot(previous, config, await loadFacts(config, previous), now)
  } catch (cause) {
    error = cause
    next = { ...stored, refresh: { ok: false, attemptedAt: now, error: errorMessage(cause) } }
  }
  await atomicWrite(snapshotPath, encodeSnapshotFile(factsOnly(next, guidance)))
  return { snapshot: combine(next, guidance), error }
}

export function errorMessage(error) {
  if (error instanceof RoadmapError) return error.message
  return `Unexpected failure: ${error?.message || error}`
}

// ---------------------------------------------------------------------------
// Findings that drive self-heal prompts

export function findings(snapshot, config) {
  const open = task => !task.referenceOnly && !task.missing && !CLOSED_STATE_TYPES.has(task.stateType)
  const laneIds = new Set((config.lanes || []).flatMap(lane => lane.ids))
  const focus = config.focus || config.phases[0].id
  const uncurated = snapshot.tasks.filter(task => open(task) && !task.curated)
  const unplaced = snapshot.tasks.filter(task => open(task) && task.curated && task.phase === focus && !laneIds.has(task.id) && task.id !== config.finalTicket?.id)
  const unknownStates = snapshot.tasks.filter(task => !task.referenceOnly && (task.unknownState || task.stateType === 'unknown'))
  const missing = snapshot.tasks.filter(task => task.missing)
  const truncated = snapshot.tasks.filter(task => task.truncated?.length)
  const emptyProjects = config.phases.flatMap(phase => phase.projects).filter(project => !snapshot.tasks.some(task => task.projectName === project))
  const danglingConfig = [...laneIds, ...Object.values(config.nextUp || {}).flat(), config.finalTicket?.id].filter(id => id && !snapshot.tasks.some(task => task.id === id))
  const review = snapshot.tasks.filter(task => open(task) && task.curated && task.reviewRequired)
  const inProgress = snapshot.tasks.filter(task => open(task) && task.stateType === 'started')
  const brief = task => ({ id: task.id, linearTitle: task.linearTitle, state: task.state, stateType: task.stateType, phase: task.phase, project: task.projectName, assignee: task.assignee, blockedBy: task.blockedBy, labels: task.labels, sourceHash: task.sourceHash })
  return {
    'integrate-new': { uncurated: uncurated.map(brief), unplaced: unplaced.map(brief), inProgress: inProgress.map(brief) },
    'reconcile-states': { unknownStates: unknownStates.map(brief), missing: missing.map(brief), truncated: truncated.map(task => ({ id: task.id, truncated: task.truncated })), emptyProjects, danglingConfig, stateTypes: snapshot.stateTypes || {} },
    'recheck-guidance': { review: review.map(task => ({ ...brief(task), title: task.title, summary: task.summary, workflow: task.workflow })) },
    custom: {},
  }
}

export function pendingCounts(snapshot, config) {
  const all = findings(snapshot, config)
  return {
    'integrate-new': all['integrate-new'].uncurated.length + all['integrate-new'].unplaced.length,
    'reconcile-states': all['reconcile-states'].unknownStates.length + all['reconcile-states'].missing.length + all['reconcile-states'].emptyProjects.length + all['reconcile-states'].danglingConfig.length,
    'recheck-guidance': all['recheck-guidance'].review.length,
  }
}

// ---------------------------------------------------------------------------
// Self-heal with headless Claude Code

export async function buildHealPrompt({ template, instruction = '', page, root, cli, snapshot, snapshotPath, config }) {
  if (!HEAL_TEMPLATES.includes(template)) throw new RoadmapError(`Unknown self-heal template: ${template}.`)
  if (template === 'custom' && !instruction.trim()) throw new RoadmapError('A custom self-heal needs an instruction.')
  const read = name => readFile(join(here, 'heal-prompts', name), 'utf8')
  const contract = await read('contract.md')
  const body = await read(`${template}.md`)
  const values = {
    page, pageRelative: relative(root, page), root, linearCli: `uv run ${cli}`,
    snapshotRelative: snapshotPath ? relative(root, snapshotPath) : '',
    contract: await readFile(join(here, '../references/page-contract.md'), 'utf8'),
    findings: JSON.stringify(findings(snapshot, config)[template], null, 1),
    instruction: instruction.trim(), product: config.product || basename(root), model: MODEL,
  }
  const fill = text => text.replace(/\{\{(\w+)\}\}/g, (_, key) => values[key] ?? '')
  return { system: fill(contract), prompt: fill(body) }
}

function summarizeTool(part) {
  const input = part.input || {}
  if (part.name === 'Bash') return `bash: ${String(input.command || '').slice(0, 160)}`
  const target = input.file_path || input.path || input.pattern
  return target ? `${part.name.toLowerCase()}: ${target}` : part.name
}

// One stream-json line from `claude -p` can carry several events (text and tool calls in one message).
export function parseClaudeEvents(line) {
  let event
  try { event = JSON.parse(line) } catch { return [] }
  if (event.type === 'assistant') {
    return (event.message?.content || []).flatMap(part => {
      if (part.type === 'tool_use') return [{ kind: 'tool', text: summarizeTool(part) }]
      if (part.type === 'text' && part.text?.trim()) return [{ kind: 'text', text: part.text.trim().slice(0, 4000) }]
      return []
    })
  }
  if (event.type === 'user') {
    return (event.message?.content || []).filter(part => part?.type === 'tool_result' && part.is_error).map(part => ({ kind: 'warn', text: `Tool call failed: ${String(typeof part.content === 'string' ? part.content : '').slice(0, 200)}` }))
  }
  if (event.type === 'result') {
    if (event.is_error || event.subtype !== 'success') return [{ kind: 'error', text: String(event.result || event.subtype || 'Claude reported an error').slice(0, 300) }]
    return [{ kind: 'end', text: 'Claude finished', result: String(event.result || '').slice(0, 4000) }]
  }
  return []
}

// Headless Claude Code in safe mode: no CLAUDE.md, skills, plugins, hooks or MCP servers. File edits and Bash are
// pre-approved; anything that would prompt is denied.
export function runClaude({ system, prompt, cwd, env, onEvent, spawnAgent = spawn, timeoutMs = LIMITS.healTimeout }) {
  return new Promise((resolvePromise, reject) => {
    const args = ['-p', '--output-format', 'stream-json', '--verbose', '--model', MODEL, '--effort', EFFORT,
      '--safe-mode', '--no-session-persistence', '--tools', 'Read,Edit,Write,Bash,Grep,Glob',
      '--permission-mode', 'acceptEdits', '--allowedTools', 'Bash', '--permission-prompts', 'none',
      '--append-system-prompt', system, prompt]
    const child = spawnAgent('claude', args, { cwd, env, detached: true, stdio: ['ignore', 'pipe', 'pipe'] })
    let buffer = '', stderrTail = '', finalText = '', failure = null, settled = false
    const kill = () => { try { process.kill(-child.pid, 'SIGKILL') } catch { try { child.kill('SIGKILL') } catch {} } }
    const timer = setTimeout(() => { failure = 'timeout'; onEvent({ kind: 'error', text: 'Time limit reached; Claude was stopped.' }); kill() }, timeoutMs)
    const handle = line => {
      if (!line.trim()) return
      for (const event of parseClaudeEvents(line)) {
        if (event.kind === 'text') finalText = event.text
        if (event.kind === 'end' && event.result) finalText = event.result
        if (event.kind === 'error') failure = failure || event.text
        onEvent(event)
      }
    }
    child.stdout.setEncoding('utf8')
    child.stdout.on('data', chunk => {
      buffer += chunk
      let newline
      while ((newline = buffer.indexOf('\n')) >= 0) { handle(buffer.slice(0, newline)); buffer = buffer.slice(newline + 1) }
    })
    child.stderr.on('data', chunk => { stderrTail = (stderrTail + chunk.toString('utf8')).slice(-4000) })
    child.on('error', error => { clearTimeout(timer); if (!settled) { settled = true; reject(new RoadmapError(`Claude Code could not start: ${error.message}. Is claude on PATH?`)) } })
    child.on('close', code => {
      clearTimeout(timer); handle(buffer)
      if (settled) return
      settled = true
      if (failure === 'timeout') return reject(new RoadmapError('Claude reached the time limit.'))
      if (failure) return reject(new RoadmapError(`Claude reported an error: ${failure}`))
      if (code !== 0) return reject(new RoadmapError(`claude exited with status ${code}. ${stderrTail.trim().split('\n').slice(-3).join(' ')}`.trim()))
      resolvePromise(finalText)
    })
  })
}

export function backupDirFor(page) {
  return join(homedir(), '.cache/roadmap-page', createHash('sha256').update(resolve(page)).digest('hex').slice(0, 16))
}

async function gitStatus(root) {
  try {
    const { stdout } = await execFileAsync('git', ['-C', root, 'status', '--porcelain', '--untracked-files=all'], { timeout: 20_000 })
    return stdout.split('\n').filter(Boolean).map(line => line.slice(3).trim())
  } catch { return null }
}

export class Healer {
  constructor({ page, root, cli, apiKey }) {
    Object.assign(this, { page, root, cli, apiKey, running: false, events: [], listeners: new Set(), lastRun: null, backups: [] })
  }
  emit(event) {
    const entry = { ...event, at: new Date().toISOString() }
    this.events.push(entry)
    if (this.events.length > LIMITS.eventLog) this.events.shift()
    for (const listener of this.listeners) listener(entry)
  }
  async backup() {
    const directory = backupDirFor(this.page)
    await mkdir(directory, { recursive: true, mode: 0o700 })
    const target = join(directory, `backup-${new Date().toISOString().replace(/[:.]/g, '-')}.html`)
    await copyFile(this.page, target)
    const existing = (await readdir(directory)).filter(name => name.startsWith('backup-')).sort()
    for (const stale of existing.slice(0, Math.max(0, existing.length - LIMITS.backups))) await unlink(join(directory, stale)).catch(() => {})
    return target
  }
  async latestBackup() {
    const directory = backupDirFor(this.page)
    try {
      const names = (await readdir(directory)).filter(name => name.startsWith('backup-')).sort()
      return names.length ? join(directory, names.at(-1)) : null
    } catch { return null }
  }
  async revert() {
    const backup = await this.latestBackup()
    if (!backup) throw new RoadmapError('There is no backup to restore.')
    const html = await readFile(backup, 'utf8')
    validatePage(html)
    await atomicWrite(this.page, html)
    await unlink(backup).catch(() => {})
    return backup
  }
  async run({ template, instruction = '', spawnAgent, dryRun = false }) {
    if (this.running) throw new RoadmapError('A self-heal is already running.')
    const { html, snapshot, snapshotPath, config } = await loadPage(this.page)
    const built = await buildHealPrompt({ template, instruction, page: this.page, root: this.root, cli: this.cli, snapshot, snapshotPath, config })
    if (dryRun) return built
    this.running = true
    this.events = []
    const startedAt = new Date().toISOString()
    this.current = { template, instruction, startedAt }
    const result = { template, instruction, startedAt, ok: false, status: 'failed', summary: '', outsideChanges: [] }
    try {
      const before = await gitStatus(this.root)
      const backup = await this.backup()
      this.emit({ kind: 'info', text: `Backup saved. Running Claude Code (${MODEL}, ${EFFORT} effort) on template "${template}".` })
      const env = { ...process.env, LINEAR_API_KEY: this.apiKey }
      const summary = await runClaude({ ...built, cwd: this.root, env, spawnAgent, onEvent: event => this.emit(event) })
      result.summary = summary
      const after = await readFile(this.page, 'utf8')
      const changed = after !== html
      try {
        validatePage(after)
      } catch (error) {
        await atomicWrite(this.page, html)
        throw new RoadmapError(`The edited page failed validation and was restored. ${error.message}`)
      }
      const statusAfter = await gitStatus(this.root)
      if (before && statusAfter) {
        const pageRelative = relative(this.root, this.page)
        result.outsideChanges = statusAfter.filter(path => !before.includes(path) && path !== pageRelative)
      }
      result.ok = true
      result.status = changed ? 'updated' : 'unchanged'
      this.emit({ kind: 'info', text: changed ? 'The page was updated and passed validation.' : 'Claude finished without changing the page.' })
      if (result.outsideChanges.length) this.emit({ kind: 'warn', text: `Claude also touched files outside the page: ${result.outsideChanges.join(', ')}. Review them with git.` })
      result.backup = backup
    } catch (error) {
      result.status = 'failed'
      result.error = errorMessage(error)
      this.emit({ kind: 'error', text: result.error })
    } finally {
      result.finishedAt = new Date().toISOString()
      this.running = false
      this.current = null
      this.lastRun = result
      await this.recordRun(result).catch(() => {})
      this.emit({ kind: 'done', text: result.status, result })
    }
    return result
  }
  async recordRun(result) {
    const { snapshotPath, stored } = await loadPage(this.page)
    stored.heal = { lastRun: { template: result.template, startedAt: result.startedAt, finishedAt: result.finishedAt, status: result.status, summary: (result.summary || result.error || '').slice(0, 2000), model: MODEL, effort: EFFORT } }
    await atomicWrite(snapshotPath, encodeSnapshotFile(stored))
  }
}

// ---------------------------------------------------------------------------
// HTTP server

function portFor(page) {
  return 4300 + parseInt(createHash('sha256').update(resolve(page)).digest('hex').slice(0, 6), 16) % 700
}

function sameOrigin(request) {
  const origin = request.headers.origin
  const host = request.headers.host
  if (request.headers['sec-fetch-site'] && request.headers['sec-fetch-site'] !== 'same-origin') return false
  if (origin && host && origin !== `http://${host}`) return false
  return true
}

function readBody(request) {
  return new Promise((resolvePromise, reject) => {
    let body = ''
    request.on('data', chunk => { body += chunk; if (body.length > 64 * 1024) reject(new RoadmapError('Request too large.')) })
    request.on('end', () => { try { resolvePromise(body ? JSON.parse(body) : {}) } catch { reject(new RoadmapError('Invalid JSON body.')) } })
    request.on('error', reject)
  })
}

function sendJson(response, status, value) {
  response.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' })
  response.end(JSON.stringify(value))
}

export function createRoadmapServer({ page, refresh, healer, pageCommand }) {
  let refreshing = false
  let lastRefresh = null
  return createServer(async (request, response) => {
    const url = new URL(request.url, 'http://localhost')
    try {
      if (request.method === 'GET' && (url.pathname === '/' || url.pathname === '/index.html')) {
        const html = await readFile(page, 'utf8')
        response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' })
        return response.end(html)
      }
      if (request.method === 'GET' && url.pathname !== '/' && !url.pathname.startsWith('/api/')) {
        const { snapshotPath } = await loadPage(page)
        if (resolve(dirname(page), '.' + decodeURIComponent(url.pathname)) === snapshotPath) {
          const text = await readFile(snapshotPath, 'utf8').catch(() => null)
          if (text === null) return sendJson(response, 404, { error: 'No snapshot yet.' })
          response.writeHead(200, { 'Content-Type': 'text/javascript; charset=utf-8', 'Cache-Control': 'no-store' })
          return response.end(text)
        }
      }
      if (request.method === 'GET' && url.pathname === '/api/status') {
        const { snapshot, config } = await loadPage(page)
        return sendJson(response, 200, {
          server: true, page: relative(healer.root, page), root: healer.root, command: pageCommand, model: MODEL, effort: EFFORT,
          refreshing, lastRefresh, heal: { running: healer.running, current: healer.current, lastRun: healer.lastRun, events: healer.events.slice(-50), hasBackup: Boolean(await healer.latestBackup()) },
          pending: pendingCounts(snapshot, config), templates: HEAL_TEMPLATES,
        })
      }
      if (request.method === 'GET' && url.pathname === '/api/heal/events') {
        response.writeHead(200, { 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-store', Connection: 'keep-alive' })
        for (const event of healer.events) response.write(`data: ${JSON.stringify(event)}\n\n`)
        const listener = event => response.write(`data: ${JSON.stringify(event)}\n\n`)
        healer.listeners.add(listener)
        const keepAlive = setInterval(() => response.write(': ping\n\n'), 15_000)
        request.on('close', () => { clearInterval(keepAlive); healer.listeners.delete(listener) })
        return
      }
      if (request.method === 'POST') {
        if (!sameOrigin(request)) return sendJson(response, 403, { error: 'Cross-origin requests are not allowed.' })
        if (url.pathname === '/api/refresh') {
          if (refreshing) return sendJson(response, 409, { error: 'A refresh is already running.' })
          if (healer.running) return sendJson(response, 409, { error: 'Wait for the self-heal to finish before refreshing.' })
          refreshing = true
          try {
            const result = await refresh()
            lastRefresh = { at: new Date().toISOString(), ok: !result.error, error: result.error ? errorMessage(result.error) : null, tickets: result.snapshot.tasks.filter(task => !task.referenceOnly).length }
            return sendJson(response, result.error ? 502 : 200, lastRefresh)
          } finally { refreshing = false }
        }
        if (url.pathname === '/api/heal') {
          if (refreshing) return sendJson(response, 409, { error: 'Wait for the refresh to finish.' })
          const body = await readBody(request)
          if (healer.running) return sendJson(response, 409, { error: 'A self-heal is already running.' })
          healer.run({ template: body.template, instruction: body.instruction || '' }).catch(() => {})
          await new Promise(done => setTimeout(done, 50))
          if (!healer.running && healer.lastRun?.status === 'failed' && healer.lastRun.startedAt >= new Date(Date.now() - 5000).toISOString()) {
            return sendJson(response, 400, { error: healer.lastRun.error })
          }
          return sendJson(response, 202, { started: true })
        }
        if (url.pathname === '/api/heal/revert') {
          if (healer.running) return sendJson(response, 409, { error: 'A self-heal is still running.' })
          const restored = await healer.revert()
          healer.lastRun = null
          return sendJson(response, 200, { restored: basename(restored) })
        }
      }
      sendJson(response, 404, { error: 'Not found.' })
    } catch (error) {
      sendJson(response, error instanceof RoadmapError ? 400 : 500, { error: errorMessage(error) })
    }
  })
}

// ---------------------------------------------------------------------------
// CLI

function argValue(argv, flag) {
  const index = argv.indexOf(flag)
  return index >= 0 ? argv[index + 1] : undefined
}

async function main(argv) {
  const positional = argv.filter((arg, index) => !arg.startsWith('--') && !['--port', '--heal', '--heal-dry', '--instruction'].includes(argv[index - 1]))
  const pageArg = positional[0]
  if (!pageArg) {
    console.error('Usage: node roadmap.mjs <page.html> [--no-open] [--refresh-only] [--check] [--port N] [--heal <template> [--instruction TEXT]] [--heal-dry <template>]')
    process.exitCode = 2
    return
  }
  const page = resolve(pageArg)
  await stat(page).catch(() => { throw new RoadmapError(`Page not found: ${page}`) })
  const root = await findProjectRoot(dirname(page))
  const cli = await findLinearCli()
  const apiKey = await resolveApiKey(root)
  const linear = makeCli({ cli, cwd: root, apiKey })
  const log = text => console.log(text)
  const refresh = () => refreshFile(page, (config, previous) => fetchFacts(linear, config, previous, log))
  const pageCommand = readConfig(await readFile(page, 'utf8')).command || `node ~/.agents/skills/roadmap-page/scripts/roadmap.mjs ${relative(root, page)}`
  const healer = new Healer({ page, root, cli, apiKey })

  if (argv.includes('--check')) {
    const { snapshot, config } = await loadPage(page)
    const next = mergeSnapshot(snapshot, config, await fetchFacts(linear, config, snapshot, log))
    const counts = pendingCounts(next, config)
    console.log(`Check passed: ${next.tasks.filter(task => !task.referenceOnly).length} roadmap tickets merged. Pending self-heal work: ${JSON.stringify(counts)}. Nothing was written.`)
    return
  }
  const dryTemplate = argValue(argv, '--heal-dry')
  if (dryTemplate) {
    const built = await healer.run({ template: dryTemplate, instruction: argValue(argv, '--instruction') || '', dryRun: true })
    console.log('--- system prompt appendix ---\n' + built.system + '\n--- prompt ---\n' + built.prompt)
    return
  }
  const healTemplate = argValue(argv, '--heal')
  if (healTemplate) {
    healer.listeners.add(event => console.log(`[${event.kind}] ${event.text}`))
    const result = await healer.run({ template: healTemplate, instruction: argValue(argv, '--instruction') || '' })
    if (result.status === 'failed') process.exitCode = 1
    return
  }

  if (!argv.includes('--no-refresh')) {
    const result = await refresh()
    if (result.error) {
      console.warn(`Could not refresh from Linear: ${errorMessage(result.error)}`)
      console.warn('Serving the last saved snapshot with a warning.')
    } else {
      const counts = pendingCounts(result.snapshot, readConfig(await readFile(page, 'utf8')))
      console.log(`Refreshed ${result.snapshot.tasks.filter(task => !task.referenceOnly).length} roadmap tickets from Linear.`)
      const pending = Object.entries(counts).filter(([, count]) => count).map(([name, count]) => `${name}: ${count}`)
      if (pending.length) console.log(`Self-heal has work waiting (${pending.join(', ')}). Use the Self-heal button on the page.`)
    }
  }
  if (argv.includes('--refresh-only')) return

  const server = createRoadmapServer({ page, refresh, healer, pageCommand })
  const requestedPort = Number(argValue(argv, '--port')) || portFor(page)
  await new Promise((resolvePromise, reject) => {
    server.once('error', error => {
      if (error.code === 'EADDRINUSE' && !argValue(argv, '--port')) { server.listen(0, '127.0.0.1', resolvePromise) } else reject(error)
    })
    server.listen(requestedPort, '127.0.0.1', resolvePromise)
  })
  const url = `http://127.0.0.1:${server.address().port}/`
  console.log(`Roadmap served at ${url} (Ctrl+C to stop).`)
  if (!argv.includes('--no-open')) execFile('open', [url], () => {})
}

// Compare real paths: the script is usually invoked through a ~/.agents/skills symlink.
function invokedDirectly() {
  try { return Boolean(process.argv[1]) && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url) } catch { return false }
}
if (invokedDirectly()) {
  main(process.argv.slice(2)).catch(error => {
    console.error(errorMessage(error))
    process.exitCode = 1
  })
}
