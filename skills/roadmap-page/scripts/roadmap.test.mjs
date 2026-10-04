import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, readFile, writeFile, mkdir } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { EventEmitter } from 'node:events'
import { PassThrough } from 'node:stream'
import {
  readSnapshot, readConfig, replaceSnapshot, validatePage, mergeSnapshot, fingerprint, findings, pendingCounts,
  resolveApiKey, makeCli, fetchFacts, parsePiEvent, runPi, buildHealPrompt, Healer, RoadmapError,
} from './roadmap.mjs'

const template = await readFile(new URL('../templates/roadmap.html', import.meta.url), 'utf8')
const config = {
  product: 'Demo', focus: 'now', ownerLabel: 'Owner Action', excludeLabelPrefixes: ['wayfinder:'],
  phases: [{ id: 'now', name: 'Now', projects: ['Alpha'] }, { id: 'next', name: 'Next', projects: ['Beta'] }],
  lanes: [{ id: 'a', name: 'A', summary: '', detail: '', ids: ['DM-1'] }], nextUp: { agent: ['DM-1'], owner: [], plan: [] },
}
const page = (snapshot = { tasks: [] }) => template.replace('{{CONFIG}}', JSON.stringify(config)).replace('{{DATA}}', JSON.stringify(snapshot))

function issue(id, overrides = {}) {
  return {
    identifier: id, title: `Title ${id}`, description: 'desc', priority: 2, estimate: 3, url: `https://linear.app/demo/issue/${id}`,
    state: { name: 'Todo', type: 'unstarted' }, project: { id: 'p1', name: 'Alpha' }, labels: [], relations: [], children: [], ...overrides,
  }
}
function facts(issues, listed = issues.map(i => i.identifier)) {
  return {
    stateTypes: { Todo: 'unstarted', Done: 'completed', 'In Progress': 'started', Weird: 'weird' },
    listed: new Map(listed.map(id => [id, { identifier: id, projectName: 'Alpha' }])),
    issues: new Map(issues.map(i => [i.identifier, i])),
  }
}

test('template renders both blocks and validates', () => {
  const html = page()
  assert.deepEqual(readSnapshot(html).tasks, [])
  assert.equal(readConfig(html).focus, 'now')
  validatePage(html)
})

test('replaceSnapshot keeps script-breaking titles as data', () => {
  const html = replaceSnapshot(page(), { tasks: [{ id: 'DM-1', title: '</script><b>' }] })
  assert.ok(!html.includes('</script><b>'))
  assert.equal(readSnapshot(html).tasks[0].title, '</script><b>')
  validatePage(html)
})

test('validatePage rejects a broken script or missing block', () => {
  assert.throws(() => validatePage(page().replace("'use strict';", "'use strict'; const = ;")), /syntax error/)
  assert.throws(() => validatePage(page().replace('id="roadmap-data"', 'id="x"')), /roadmap-data/)
})

test('merge creates uncurated tasks, derives phase, owner and blockers, and pulls reference blockers', () => {
  const snapshot = mergeSnapshot({ tasks: [] }, config, facts([
    issue('DM-1', { relations: [{ type: 'blocked-by', issue: 'DM-9' }, { type: 'related', issue: 'DM-2' }] }),
    issue('DM-2', { labels: [{ name: 'Owner Action' }], project: { id: 'p2', name: 'Beta' } }),
    issue('DM-9', { project: { id: 'p3', name: 'Other' } }),
  ], ['DM-1', 'DM-2']), '2026-10-04T00:00:00.000Z')
  const byId = Object.fromEntries(snapshot.tasks.map(t => [t.id, t]))
  assert.deepEqual(byId['DM-1'].blockedBy, ['DM-9'])
  assert.equal(byId['DM-1'].curated, false)
  assert.equal(byId['DM-1'].reviewRequired, true)
  assert.equal(byId['DM-2'].phase, 'next')
  assert.equal(byId['DM-2'].owner, true)
  assert.equal(byId['DM-2'].workflow, 'owner')
  assert.equal(byId['DM-9'].referenceOnly, true)
  assert.equal(byId['DM-9'].phase, 'later')
  assert.equal(snapshot.refresh.ok, true)
})

test('merge preserves curated text and only flags review on substantive changes', () => {
  const base = issue('DM-1')
  const first = mergeSnapshot({ tasks: [] }, config, facts([base]))
  first.tasks[0] = { ...first.tasks[0], title: 'Nice name', summary: 'S', curated: true, reviewedHash: first.tasks[0].sourceHash, gates: ['DM-5'] }
  const routine = mergeSnapshot(first, config, facts([
    issue('DM-1', { state: { name: 'In Progress', type: 'started' }, assignee: { name: 'Ro' }, estimate: 5 }),
    issue('DM-5', { state: { name: 'Done', type: 'completed' } }),
  ], ['DM-1']))
  const task = routine.tasks.find(t => t.id === 'DM-1')
  assert.equal(task.title, 'Nice name')
  assert.equal(task.reviewRequired, false)
  assert.equal(task.stateType, 'started')
  assert.equal(task.assignee, 'Ro')
  assert.ok(routine.tasks.some(t => t.id === 'DM-5' && t.referenceOnly))
  const substantive = mergeSnapshot(first, config, facts([issue('DM-1', { description: 'changed' })]))
  assert.equal(substantive.tasks[0].reviewRequired, true)
  assert.equal(substantive.tasks[0].title, 'Nice name')
})

test('fingerprint ignores status and comments but tracks labels and blockers', () => {
  const a = fingerprint(issue('DM-1'), [], 'Owner Action')
  assert.equal(a, fingerprint(issue('DM-1', { state: { name: 'Done', type: 'completed' }, assignee: { name: 'x' } }), [], 'Owner Action'))
  assert.notEqual(a, fingerprint(issue('DM-1'), ['DM-2'], 'Owner Action'))
  assert.notEqual(a, fingerprint(issue('DM-1', { labels: [{ name: 'Owner Action' }] }), [], 'Owner Action'))
})

test('unknown states, missing tickets and excluded labels are handled', () => {
  const previous = { tasks: [{ id: 'DM-7', title: 'Gone', curated: true, blockedBy: [], gates: [], referenceOnly: false }] }
  const snapshot = mergeSnapshot(previous, config, facts([
    issue('DM-1', { state: { name: 'Weird', type: 'weird' } }),
    issue('DM-3', { labels: [{ name: 'wayfinder:map' }] }),
  ], ['DM-1', 'DM-3']))
  const byId = Object.fromEntries(snapshot.tasks.map(t => [t.id, t]))
  assert.equal(byId['DM-1'].unknownState, true)
  assert.equal(byId['DM-7'].missing, true)
  assert.equal(byId['DM-7'].title, 'Gone')
  assert.equal(byId['DM-3'], undefined)
  const found = findings(snapshot, config)
  assert.equal(found['reconcile-states'].unknownStates[0].id, 'DM-1')
  assert.equal(found['reconcile-states'].missing[0].id, 'DM-7')
  assert.deepEqual(found['reconcile-states'].emptyProjects, ['Beta'])
  assert.equal(pendingCounts(snapshot, config)['integrate-new'], 1)
})

test('resolveApiKey follows the project env precedence', async () => {
  const root = await mkdtemp(join(tmpdir(), 'roadmap-env-'))
  await mkdir(join(root, '.agents'), { recursive: true })
  await mkdir(join(root, '.pi'), { recursive: true })
  await writeFile(join(root, '.agents/env.json'), JSON.stringify({ LINEAR_API_KEY: 'agents' }))
  assert.equal(await resolveApiKey(root, { LINEAR_API_KEY: 'shell' }), 'agents')
  await writeFile(join(root, '.pi/env.json'), JSON.stringify({ LINEAR_API_KEY: null }))
  await assert.rejects(resolveApiKey(root, { LINEAR_API_KEY: 'shell' }, () => {}), RoadmapError)
  await writeFile(join(root, '.pi/env.json'), '{bad json')
  assert.equal(await resolveApiKey(root, {}, () => {}), 'agents')
})

test('makeCli surfaces CLI error envelopes and fetchFacts follows blockers across pages', async () => {
  const calls = []
  const responses = {
    'states': { teams: [{ states: [{ name: 'Todo', type: 'unstarted' }] }] },
    'list Alpha': { issues: [{ identifier: 'DM-1' }], pageInfo: { hasNextPage: true, endCursor: 'c1' } },
    'list Alpha c1': { issues: [{ identifier: 'DM-2' }], pageInfo: { hasNextPage: false } },
    'list Beta': { issues: [], pageInfo: { hasNextPage: false } },
    'get DM-1': issue('DM-1', { relations: [{ type: 'blocked-by', issue: 'DM-9' }] }),
    'get DM-2': issue('DM-2'),
    'get DM-9': null,
  }
  const run = async (_uv, args) => {
    // args = ['run', cli, command, ...options]
    const key = args[2] === 'list' ? ['list', args[4], ...(args.includes('--after') ? [args[args.indexOf('--after') + 1]] : [])].join(' ') : args.slice(2, 4).join(' ')
    calls.push(key)
    if (key === 'get DM-9') return { stdout: JSON.stringify({ success: false, command: 'get', error: { code: 'ISSUE_NOT_FOUND', message: 'Entity not found: Issue' } }) }
    return { stdout: JSON.stringify({ success: true, result: responses[key] }) }
  }
  const linear = makeCli({ cli: 'linear.py', cwd: '/', apiKey: 'k', run })
  const result = await fetchFacts(linear, config, { tasks: [] })
  assert.deepEqual([...result.listed.keys()], ['DM-1', 'DM-2'])
  assert.equal(result.issues.get('DM-9'), null)
  assert.ok(calls.includes('get DM-9'))
  const failing = makeCli({ cli: 'linear.py', cwd: '/', apiKey: 'k', run: async () => ({ stdout: JSON.stringify({ success: false, error: { code: 'MISSING_API_KEY', message: 'nope' } }) }) })
  await assert.rejects(failing(['states']), /MISSING_API_KEY/)
})

test('parsePiEvent summarises tools, text and errors', () => {
  assert.deepEqual(parsePiEvent(JSON.stringify({ type: 'tool_execution_start', toolName: 'bash', args: { command: 'uv run linear.py get X' } })), { kind: 'tool', text: 'bash: uv run linear.py get X' })
  assert.deepEqual(parsePiEvent(JSON.stringify({ type: 'tool_execution_start', toolName: 'edit', args: { path: 'etc/r.html' } })), { kind: 'tool', text: 'edit: etc/r.html' })
  assert.deepEqual(parsePiEvent(JSON.stringify({ type: 'message_end', message: { role: 'assistant', stopReason: 'stop', content: [{ type: 'text', text: 'Done.' }] } })), { kind: 'text', text: 'Done.' })
  assert.equal(parsePiEvent(JSON.stringify({ type: 'message_end', message: { role: 'assistant', stopReason: 'error', errorMessage: 'quota' } })).kind, 'error')
  assert.equal(parsePiEvent('not json'), null)
})

function fakeSpawn({ lines = [], stderr = '', code = 0 }) {
  return () => {
    const child = new EventEmitter()
    child.pid = 12345
    child.stdout = new PassThrough(); child.stderr = new PassThrough()
    child.kill = () => {}
    setTimeout(() => {
      for (const line of lines) child.stdout.write(JSON.stringify(line) + '\n')
      if (stderr) child.stderr.write(stderr)
      child.stdout.end(); child.stderr.end()
      child.emit('close', code)
    }, 5)
    return child
  }
}

test('runPi resolves the final assistant text and maps trust failures', async () => {
  const events = []
  const text = await runPi({ system: 's', prompt: 'p', cwd: '/', env: {}, onEvent: e => events.push(e), spawnPi: fakeSpawn({ lines: [
    { type: 'tool_execution_start', toolName: 'read', args: { path: 'x' } },
    { type: 'message_end', message: { role: 'assistant', stopReason: 'stop', content: [{ type: 'text', text: 'All good' }] } },
    { type: 'agent_end' },
  ] }) })
  assert.equal(text, 'All good')
  assert.deepEqual(events.map(e => e.kind), ['tool', 'text', 'end'])
  await assert.rejects(runPi({ system: 's', prompt: 'p', cwd: '/', env: {}, onEvent: () => {}, spawnPi: fakeSpawn({ stderr: 'safe-pi: non-interactive shell and project is not trusted; aborting', code: 1 }) }), /safe-pi-trust/)
  await assert.rejects(runPi({ system: 's', prompt: 'p', cwd: '/', env: {}, onEvent: () => {}, spawnPi: fakeSpawn({ code: 3 }) }), /status 3/)
})

test('buildHealPrompt fills findings and rejects empty custom instructions', async () => {
  const snapshot = mergeSnapshot({ tasks: [] }, config, facts([issue('DM-1')]))
  const built = await buildHealPrompt({ template: 'integrate-new', page: '/p/etc/r.html', root: '/p', cli: '/cli/linear.py', snapshot, config })
  assert.match(built.prompt, /"DM-1"/)
  assert.match(built.system, /etc\/r\.html/)
  assert.match(built.system, /uv run \/cli\/linear\.py/)
  await assert.rejects(buildHealPrompt({ template: 'custom', page: '/p/r.html', root: '/p', cli: 'c', snapshot, config }), /instruction/)
  await assert.rejects(buildHealPrompt({ template: 'nope', page: '/p/r.html', root: '/p', cli: 'c', snapshot, config }), /Unknown/)
})

test('Healer restores the page when the edited result fails validation and records the run', async () => {
  const root = await mkdtemp(join(tmpdir(), 'roadmap-heal-'))
  const pagePath = join(root, 'r.html')
  const snapshot = mergeSnapshot({ tasks: [] }, config, facts([issue('DM-1')]))
  await writeFile(pagePath, page(snapshot))
  const healer = new Healer({ page: pagePath, root, cli: 'c', apiKey: 'k' })
  const breakPage = () => {
    const spawn = fakeSpawn({ lines: [{ type: 'message_end', message: { role: 'assistant', stopReason: 'stop', content: [{ type: 'text', text: 'broke it' }] } }] })
    return (...args) => { writeFile(pagePath, '<html>oops</html>'); return spawn(...args) }
  }
  const result = await healer.run({ template: 'integrate-new', spawnPi: breakPage() })
  assert.equal(result.status, 'failed')
  assert.match(result.error, /restored/)
  const restored = await readFile(pagePath, 'utf8')
  validatePage(restored)
  assert.equal(readSnapshot(restored).heal.lastRun.status, 'failed')
  const ok = await healer.run({ template: 'integrate-new', spawnPi: fakeSpawn({ lines: [{ type: 'message_end', message: { role: 'assistant', stopReason: 'stop', content: [{ type: 'text', text: 'No change needed' }] } }] }) })
  assert.equal(ok.status, 'unchanged')
  assert.equal(ok.summary, 'No change needed')
  assert.ok(await healer.latestBackup())
})
