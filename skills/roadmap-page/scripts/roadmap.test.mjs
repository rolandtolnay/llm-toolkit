import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, readFile, writeFile, mkdir } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { EventEmitter } from 'node:events'
import { PassThrough } from 'node:stream'
import {
  readGuidance, readConfig, encodeSnapshotFile, parseSnapshotFile, readSnapshotFile, refreshFile, loadPage, validatePage, mergeSnapshot, fingerprint, findings, pendingCounts,
  resolveApiKey, makeCli, fetchFacts, parseClaudeEvents, runClaude, buildHealPrompt, Healer, RoadmapError,
} from './roadmap.mjs'

const template = await readFile(new URL('../templates/roadmap.html', import.meta.url), 'utf8')
const config = {
  product: 'Demo', focus: 'now', ownerLabel: 'Owner Action', excludeLabelPrefixes: ['wayfinder:'],
  phases: [{ id: 'now', name: 'Now', projects: ['Alpha'] }, { id: 'next', name: 'Next', projects: ['Beta'] }],
  lanes: [{ id: 'a', name: 'A', summary: '', detail: '', ids: ['DM-1'] }], nextUp: { agent: ['DM-1'], owner: [], plan: [] },
}
const page = (guidance = { tasks: [] }) => template.replace('{{CONFIG}}', JSON.stringify(config)).replace('{{GUIDANCE}}', JSON.stringify(guidance)).replace('{{SNAPSHOT}}', 'r.snapshot.js')

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
  assert.deepEqual(readGuidance(html).tasks, [])
  assert.equal(readConfig(html).focus, 'now')
  validatePage(html)
})

test('the snapshot file keeps script-breaking titles as data', () => {
  const text = encodeSnapshotFile({ tasks: [{ id: 'DM-1', title: '</script><b>\u2028' }] })
  assert.ok(!text.includes('</script>'))
  assert.equal(parseSnapshotFile(text).tasks[0].title, '</script><b>\u2028')
  assert.throws(() => parseSnapshotFile('window.OTHER = {};'), RoadmapError)
})

test('validatePage rejects a broken script or missing block', () => {
  assert.throws(() => validatePage(page().replace("'use strict';", "'use strict'; const = ;")), /syntax error/)
  assert.throws(() => validatePage(page().replace('id="roadmap-guidance"', 'id="x"')), /roadmap-guidance/)
  assert.throws(() => validatePage(page().replace('id="roadmap-snapshot"', 'id="x"')), /roadmap-snapshot/)
})

test('refresh writes only the snapshot file, and page guidance decides curation and tracking', async () => {
  const root = await mkdtemp(join(tmpdir(), 'roadmap-split-'))
  const pagePath = join(root, 'r.html')
  const first = mergeSnapshot({ tasks: [] }, config, facts([issue('DM-1'), issue('DM-2')]))
  const hash = first.tasks.find(t => t.id === 'DM-1').sourceHash
  const html = page({ tasks: [{ id: 'DM-1', title: 'Nice name', summary: 'S', detail: 'D', input: 'I', workflow: 'scope', gates: [], curated: true, reviewedHash: hash }] })
  await writeFile(pagePath, html)
  assert.deepEqual((await loadPage(pagePath)).snapshot.tasks.map(t => t.id), ['DM-1'])

  await refreshFile(pagePath, async () => facts([issue('DM-1'), issue('DM-2')]))
  assert.equal(await readFile(pagePath, 'utf8'), html)
  const stored = await readSnapshotFile(join(root, 'r.snapshot.js'))
  const storedById = Object.fromEntries(stored.tasks.map(t => [t.id, t]))
  assert.equal(storedById['DM-1'].title, undefined)
  assert.equal(storedById['DM-1'].reviewRequired, undefined)
  assert.equal(storedById['DM-2'].curated, false)
  const loaded = Object.fromEntries((await loadPage(pagePath)).snapshot.tasks.map(t => [t.id, t]))
  assert.equal(loaded['DM-1'].title, 'Nice name')
  assert.equal(loaded['DM-1'].reviewRequired, false)
  assert.equal(loaded['DM-2'].reviewRequired, true)

  // Unlisted tickets stay only while the page has guidance for them.
  const { snapshot } = await refreshFile(pagePath, async () => facts([issue('DM-1'), issue('DM-2')], []))
  assert.deepEqual(snapshot.tasks.map(t => t.id), ['DM-1'])
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

test('next-phase findings name the first later phase with open work once the focus phase is done', () => {
  const beta = { project: { id: 'p2', name: 'Beta' } }
  const open = mergeSnapshot({ tasks: [] }, config, facts([issue('DM-1'), issue('DM-2', beta)]))
  assert.equal(findings(open, config)['next-phase'].next, 'next')
  assert.deepEqual(findings(open, config)['next-phase'].candidates.map(task => task.id), ['DM-2'])
  assert.equal(pendingCounts(open, config)['next-phase'], 0)
  const done = mergeSnapshot({ tasks: [] }, config, facts([issue('DM-1', { state: { name: 'Done', type: 'completed' } }), issue('DM-2', beta)]))
  assert.equal(findings(done, config)['next-phase'].remaining.length, 0)
  assert.equal(pendingCounts(done, config)['next-phase'], 1)
  const last = mergeSnapshot({ tasks: [] }, config, facts([issue('DM-1')]))
  assert.equal(findings(last, config)['next-phase'].next, null)
  assert.equal(pendingCounts(last, config)['next-phase'], 0)
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

test('makeCli surfaces CLI error envelopes and fetchFacts follows blockers across pages and reads milestones', async () => {
  const calls = []
  const responses = {
    'states': { teams: [{ states: [{ name: 'Todo', type: 'unstarted' }] }] },
    'list Alpha': { issues: [{ identifier: 'DM-1' }], pageInfo: { hasNextPage: true, endCursor: 'c1' } },
    'list Alpha c1': { issues: [{ identifier: 'DM-2' }], pageInfo: { hasNextPage: false } },
    'list Beta': { issues: [], pageInfo: { hasNextPage: false } },
    'get DM-1': issue('DM-1', { relations: [{ type: 'blocked-by', issue: 'DM-9' }] }),
    'get DM-2': issue('DM-2'),
    'get DM-9': null,
    'milestones Alpha': { project: 'Alpha', milestones: [{ id: 'm1', name: 'Beta ready', status: 'next', targetDate: '2026-10-14', description: 'x' }, { id: 'm2', name: 'Published', status: 'unstarted' }] },
    'milestones Beta': { project: 'Beta', milestones: [] },
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
  assert.deepEqual(result.milestones, [
    { project: 'Alpha', name: 'Beta ready', targetDate: '2026-10-14', status: 'next' },
    { project: 'Alpha', name: 'Published', targetDate: null, status: 'unstarted' },
  ])
  assert.deepEqual(mergeSnapshot({ tasks: [] }, config, result).milestones, result.milestones)
  const failing = makeCli({ cli: 'linear.py', cwd: '/', apiKey: 'k', run: async () => ({ stdout: JSON.stringify({ success: false, error: { code: 'MISSING_API_KEY', message: 'nope' } }) }) })
  await assert.rejects(failing(['states']), /MISSING_API_KEY/)
})

const assistant = (...content) => ({ type: 'assistant', message: { content } })
const done = text => ({ type: 'result', subtype: 'success', is_error: false, result: text })

test('parseClaudeEvents summarises tools, text, failed tools and the result', () => {
  assert.deepEqual(parseClaudeEvents(JSON.stringify(assistant(
    { type: 'text', text: 'Reading.' },
    { type: 'tool_use', name: 'Bash', input: { command: 'uv run linear.py get X' } },
    { type: 'tool_use', name: 'Edit', input: { file_path: 'etc/r.html' } },
  ))), [{ kind: 'text', text: 'Reading.' }, { kind: 'tool', text: 'bash: uv run linear.py get X' }, { kind: 'tool', text: 'edit: etc/r.html' }])
  assert.equal(parseClaudeEvents(JSON.stringify({ type: 'user', message: { content: [{ type: 'tool_result', is_error: true, content: 'denied' }] } }))[0].kind, 'warn')
  assert.deepEqual(parseClaudeEvents(JSON.stringify(done('All good'))), [{ kind: 'end', text: 'Claude finished', result: 'All good' }])
  assert.equal(parseClaudeEvents(JSON.stringify({ type: 'result', subtype: 'error_max_turns', is_error: true }))[0].kind, 'error')
  assert.deepEqual(parseClaudeEvents('not json'), [])
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

test('runClaude resolves the final result text and reports errors and exit codes', async () => {
  const events = []
  const text = await runClaude({ system: 's', prompt: 'p', cwd: '/', env: {}, onEvent: e => events.push(e), spawnAgent: fakeSpawn({ lines: [
    assistant({ type: 'tool_use', name: 'Read', input: { file_path: 'x' } }),
    assistant({ type: 'text', text: 'Interim' }),
    done('All good'),
  ] }) })
  assert.equal(text, 'All good')
  assert.deepEqual(events.map(e => e.kind), ['tool', 'text', 'end'])
  await assert.rejects(runClaude({ system: 's', prompt: 'p', cwd: '/', env: {}, onEvent: () => {}, spawnAgent: fakeSpawn({ lines: [{ type: 'result', subtype: 'error_during_execution', is_error: true, result: 'quota' }], code: 1 }) }), /quota/)
  await assert.rejects(runClaude({ system: 's', prompt: 'p', cwd: '/', env: {}, onEvent: () => {}, spawnAgent: fakeSpawn({ code: 3 }) }), /status 3/)
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
  await writeFile(pagePath, page())
  const healer = new Healer({ page: pagePath, root, cli: 'c', apiKey: 'k' })
  const breakPage = () => {
    const spawn = fakeSpawn({ lines: [done('broke it')] })
    return (...args) => { writeFile(pagePath, '<html>oops</html>'); return spawn(...args) }
  }
  const result = await healer.run({ template: 'integrate-new', spawnAgent: breakPage() })
  assert.equal(result.status, 'failed')
  assert.match(result.error, /restored/)
  const restored = await readFile(pagePath, 'utf8')
  validatePage(restored)
  assert.equal((await readSnapshotFile(join(root, 'r.snapshot.js'))).heal.lastRun.status, 'failed')
  const ok = await healer.run({ template: 'integrate-new', spawnAgent: fakeSpawn({ lines: [done('No change needed')] }) })
  assert.equal(ok.status, 'unchanged')
  assert.equal(ok.summary, 'No change needed')
  assert.ok(await healer.latestBackup())
})
