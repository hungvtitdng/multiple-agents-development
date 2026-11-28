import { expect, test } from 'claude-code/testing'

const PANE = {
  plugin: 'agent-team',
  component: 'Pane',
  requestId: 'team-panel',
  props: {
    title: 'Agent team',
    isFocused: false,
    bodyColumns: 48,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 40 },
    view: {},
  },
} as const

const RUN = { role: 'backend-dev', state: 'RUNNING', tool: 'Bash: npm test', idle: 800, hung: true, result: '' }
const VIEW = {
  now: 120000,
  board: {
    stage: 'S4',
    task: 'H1',
    steps: [
      { n: '1', state: 'done', title: 'Scan KB', role: 'scout' },
      { n: '2', state: 'doing', title: 'Code BE', role: 'backend-dev' },
    ],
    runs: [RUN, { role: 'scout', state: 'DONE', tool: '', idle: 5, hung: false, result: 'KB ok' }],
    debate: { run: 'S2-R1', posts: 5, whys: 2, votes: 3 },
    tasks: [
      { id: 'JR-1', stage: 'S4', session: 'run', steps: '1/2', agents: [{ ...RUN, role: 'test-executor', hung: false }] },
      { id: 'JR-4', stage: 'S3', session: 'ask', steps: '0/2', agents: [] },
    ],
    queue: ['JR-3'],
    modules: [
      { module: 'M-1', title: 'Login', state: 'SPLIT', done: 1, total: 2, running: 1 },
      { module: 'M-2', title: 'Orders', state: 'DONE', done: 1, total: 1, running: 0 },
    ],
  },
  rows: [
    { id: 'a', name: 'scout', title: 'Scan the KB', status: 'completed', label: '', tool: '', toolAt: 0, startTime: 0, endedAt: 30000, tokens: 1200, usd: 0.1 },
    { id: 'b', parentId: 'a', name: 'backend-dev', title: 'Code the API', status: 'running', label: 'x', tool: 'Bash: npm test', toolAt: 40000, startTime: 40000, tokens: 45000, usd: 0.4 },
  ],
  main: { model: 'claude-fable-5-2', percent: 36, tokens: 356000, window: 1000000, usd: 14.48, limits: [{ kind: 'five_hour', percent: 9 }] },
  lead: { since: 60000, tool: 'Edit', calls: 4, requests: 22, effort: 'high' },
  last: { ms: 12000, agents: 1, edits: 3, errors: 0, usd: 0.21 },
  log: [{ at: 0, who: 'scout', text: 'started' }],
}

test('the pane draws every block from a stored view', async ($, on) => {
  on('state.get', () => ({ value: { value: { shape: 'view-7', value: VIEW }, version: 1 } }))

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    const wanted = [
      /AGENT TEAM · /,
      /FABLE 5\.2/,
      /1 AGENT HUNG/,
      /^MAIN$/,
      / · working 1:00/,
      /^Fable 5\.2$/,
      /» Edit · 4 tools/,
      /22 req/,
      /\$14\.48/,
      /^TASKS$/,
      /1 waiting/,
      /1 queued/,
      /JR-4 S3 · 0\/2 steps · needs your answer/,
      /test-executor · Bash: npm test/,
      /^MODULES$/,
      /M-1 Login/,
      /1\/2/,
      /^TASK$/,
      / · H1 s4/,
      /Code BE/,
      /» debate S2-R1 · 5 posts · 2 WHY open · 3 votes/,
      /^AGENTS$/,
      / · 1 running/,
      /1 done/,
      /1 failed/,
      /1: Scan the KB/,
      /└2: Code the API/,
      /backend-dev · HUNG, silent 13m/,
      /scout · 1\.2k tok · \$0\.10 · KB ok/,
      /» last turn 0:12 · 1 agents · \+\$0\.21/,
      /edits: 3/,
      /^ · /,
      /^SESSION$/,
      / · log/,
      /^●▬+$/,
      /─/,
    ]
    const missing = []
    for (const text of wanted) {
      if (!(await ui.find({ type: 'Text', text }))) missing.push(String(text))
    }
    expect(missing).toEqual([])
    await ui.unmount()
  }
})

test('an empty view still draws', async $ => {
  const ui = await $.ui.mount({ ...PANE, surface: 'terminal' })

  expect(await ui.find({ type: 'Text', text: / IDLE/ })).toBeDefined()
  expect(await ui.find({ type: 'Text', text: /TASK · / })).toBeUndefined()
  expect(await ui.find({ type: 'Text', text: /No agents yet/ })).toBeDefined()
  await ui.unmount()
})
