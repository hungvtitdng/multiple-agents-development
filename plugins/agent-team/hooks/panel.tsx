import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Board, Lead, LogLine, Main, Row, Turn, View } from '../types'

const PANE = 'team-panel'
const TITLE = 'Agent team'
const OPEN = { id: PANE, title: TITLE, backgroundColor: 'transparent' } as const
const LIVE = new Set(['pending', 'running', 'waiting', 'idle'])
const BAD = new Set(['failed', 'killed'])
const MARK: Record<string, string> = { doing: '▶', done: '✓', skip: '–', todo: '○' }
const SESSION: Record<string, string> = { run: '▶', ask: '⏸', done: '✓', none: '■' }
const SESSION_NOTE: Record<string, string> = { ask: 'needs your answer', done: 'done', none: 'session stopped' }
const LIMIT_NAME: Record<string, string> = { five_hour: '5h', seven_day: '7d', spend_limit: 'spend' }
const NAME_WIDTH = 16
const TITLE_WIDTH = 18
const EDITS = new Set(['Edit', 'Write', 'MultiEdit', 'NotebookEdit'])
const EFFORT: Record<string, number> = { low: 1, medium: 2, high: 3, xhigh: 4, max: 4 }
const COLLECT = String.raw`import glob, json, os, re, sqlite3, subprocess, sys, time

root = sys.argv[1]
now = int(time.time())


def cfg(key, default):
    for name in ("agent-team.local.config", "agent-team.config"):
        try:
            for line in open(os.path.join(root, ".claude", name), encoding="utf-8", errors="ignore"):
                m = re.match(r"^\s*" + key + r"=\s*['\"]?([^'\"#\s]+)", line)
                if m:
                    return m.group(1)
        except OSError:
            pass
    return default


def text(path):
    try:
        return open(path, encoding="utf-8", errors="ignore").read().strip()
    except OSError:
        return ""


hang = int(cfg("HANG_MINUTES", "10")) * 60


def board(base):
    out = {"stage": text(os.path.join(base, ".agent-team", "stage")).upper(), "task": "", "steps": [], "runs": [],
           "debate": {"run": "", "posts": 0, "whys": 0, "votes": 0}}
    path = os.path.join(base, ".agent-team", "board.db")
    if not os.path.isfile(path):
        return out
    try:
        db = sqlite3.connect("file:" + path + "?mode=ro", uri=True, timeout=2)
        row = db.execute("SELECT task FROM plan_steps ORDER BY rowid DESC LIMIT 1").fetchone() or \
            db.execute("SELECT task FROM agent_runs ORDER BY last_seen DESC LIMIT 1").fetchone()
        if not row:
            return out
        task = out["task"] = row[0]
        out["steps"] = [{"n": str(n), "state": s, "title": t, "role": r or ""} for n, s, t, r in
                        db.execute("SELECT n, state, title, role FROM plan_steps WHERE task=? ORDER BY n", (task,))]
        seen = set()
        for role, state, tool, last, busy, tmo, result in db.execute(
                "SELECT role, state, last_tool, last_seen, busy_since, tool_timeout, result FROM agent_runs "
                "WHERE task=? AND last_seen > ? ORDER BY last_seen DESC", (task, now - 6 * 3600)):
            if role in seen:
                continue
            seen.add(role)
            alive = last > now - hang or (busy is not None and last + (tmo or 0) + 60 > now)
            out["runs"].append({"role": role, "state": state, "tool": tool or "", "idle": now - last,
                                "hung": state != "DONE" and not alive, "result": (result or "").split("\n")[0][:120]})
        rnd = db.execute("SELECT stage, round FROM rounds WHERE task=? AND closed_at IS NULL ORDER BY id DESC LIMIT 1", (task,)).fetchone()
        if rnd:
            out["debate"] = {
                "run": "%s-R%s" % rnd,
                "posts": db.execute("SELECT count(*) FROM messages WHERE task=? AND stage=? AND round=?", (task, *rnd)).fetchone()[0],
                "whys": db.execute("SELECT count(*) FROM whys WHERE task=? AND status IN ('open','voting')", (task,)).fetchone()[0],
                "votes": db.execute("SELECT count(*) FROM votes WHERE why_id IN (SELECT id FROM whys WHERE task=? AND status IN ('open','voting'))", (task,)).fetchone()[0],
            }
        db.close()
    except sqlite3.Error:
        pass
    return out


out = board(root)
wdir = os.path.join(root, cfg("WORKTREE_DIR", ".worktrees"))
try:
    rows = json.loads(subprocess.run([os.environ.get("AGENT_TEAM_CLAUDE", "claude"), "agents", "--json"],
                                     capture_output=True, text=True, timeout=4).stdout)
except (OSError, ValueError, subprocess.SubprocessError):
    rows = []
live = {os.path.basename(x["cwd"]): x.get("status") for x in rows
        if x.get("kind") == "background" and os.path.dirname(os.path.realpath(x.get("cwd") or "/")) == os.path.realpath(wdir)}
out["tasks"] = []
for side in sorted(glob.glob(os.path.join(wdir, "*", ".agent-team", "side"))):
    base = os.path.dirname(os.path.dirname(side))
    b = board(base)
    tid = os.path.basename(base)
    session = "none" if tid not in live else "run" if live[tid] == "busy" else "done" if b["stage"] == "S6" else "ask"
    done = len([s for s in b["steps"] if s["state"] in ("done", "skip")])
    out["tasks"].append({"id": tid, "stage": b["stage"], "session": session, "steps": "%d/%d" % (done, len(b["steps"])),
                         "agents": [r for r in b["runs"] if r["state"] != "DONE"]})
out["queue"] = text(os.path.join(root, ".agent-team", "batch-queue")).split()
out["modules"] = []
try:
    db = sqlite3.connect("file:" + os.path.join(root, ".agent-team", "board.db") + "?mode=ro", uri=True, timeout=2)
    for mod, title, state, done, total, busy in db.execute(
            "SELECT m.module, COALESCE(m.title, ''), m.state, "
            "(SELECT count(*) FROM pool p WHERE p.module = m.module AND p.state = 'DONE'), "
            "(SELECT count(*) FROM pool p WHERE p.module = m.module), "
            "(SELECT count(*) FROM pool p WHERE p.module = m.module AND p.state IN ('RUNNING', 'FIX', 'GAP')) "
            "FROM pool_modules m ORDER BY m.ord, m.module"):
        out["modules"].append({"module": mod, "title": title, "state": state, "done": done, "total": total, "running": busy})
    db.close()
except sqlite3.Error:
    pass
print(json.dumps(out))
`
const NO_BOARD: Board = {
  stage: '',
  task: '',
  steps: [],
  runs: [],
  debate: { run: '', posts: 0, whys: 0, votes: 0 },
  tasks: [],
  queue: [],
  modules: [],
}
const NO_MAIN: Main = { model: '', percent: 0, tokens: 0, window: 0, usd: 0, limits: [] }
const NO_LEAD: Lead = { since: 0, tool: '', calls: 0, requests: 0, effort: '' }
const NO_TURN: Turn = { ms: 0, agents: 0, edits: 0, errors: 0, usd: 0 }
const EMPTY: View = { now: 0, board: NO_BOARD, rows: [], main: NO_MAIN, lead: NO_LEAD, last: NO_TURN, log: [] }

const view = atom({ plugin: 'agent-team', key: 'view' } as const, EMPTY, { shape: 'view-7' })

const tools: Record<string, { text: string; at: number }> = {}
const lead: Lead = { ...NO_LEAD }
const pending: LogLine[] = []
const turn = { ...NO_TURN, usdAt: 0 }
let last: Turn = NO_TURN

const spent = async ($: EngineInterface) => (await $.session.usage().catch(() => undefined))?.cost?.usd ?? 0

const modelName = (id: string) => {
  const [name = '', ...rest] = id.replace(/^claude-/, '').split('-')

  return `${name.charAt(0).toUpperCase()}${name.slice(1)} ${rest.filter(x => /^\d+$/.test(x)).join('.')}`.trim()
}

const clock = (ms: number) => {
  const s = Math.max(0, Math.floor(ms / 1000))

  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

const span = (ms: number) => {
  const m = Math.max(0, Math.round(ms / 60000))

  return m >= 1440 ? `${Math.floor(m / 1440)}d${Math.floor((m % 1440) / 60)}h` : m >= 60 ? `${Math.floor(m / 60)}h${m % 60}m` : `${m}m`
}

const timeOfDay = (ms: number) => {
  const d = new Date(ms)

  return [d.getHours(), d.getMinutes(), d.getSeconds()].map(n => String(n).padStart(2, '0')).join(':')
}

const short = (n: number) =>
  n >= 1000000 ? `${(n / 1000000).toFixed(1)}M` : n >= 1000 ? `${(n / 1000).toFixed(n >= 100000 ? 0 : 1)}k` : String(n)

const meter = (percent: number, width: number) => {
  const filled = Math.max(0, Math.min(width, Math.round((percent / 100) * width)))

  return '▰'.repeat(filled) + '▱'.repeat(width - filled)
}

const readBoard = async ($: EngineInterface, cwd: string): Promise<Board> => {
  try {
    const out = await $.process.run(['python3', '-c', COLLECT, cwd], { timeoutMs: 8000 })

    return out.exitCode === 0 ? { ...NO_BOARD, ...(JSON.parse(out.stdout) as Board) } : NO_BOARD
  } catch {
    return NO_BOARD
  }
}

const readMain = async ($: EngineInterface): Promise<Main> => {
  const [usage, model] = await Promise.all([$.session.usage(), $.session.model()])

  return {
    model,
    percent: usage.context.percent ?? 0,
    tokens: usage.context.tokens ?? 0,
    window: usage.context.window,
    usd: usage.cost?.usd ?? 0,
    limits: usage.rateLimits.map(l => ({ kind: l.kind, percent: l.percentUsed, resetsAt: l.resetsAt })),
  }
}

const boardLog = (old: Board, next: Board, now: number): LogLine[] => {
  const log: LogLine[] = []
  if (next.stage && next.stage !== old.stage) log.push({ at: now, who: 'lead', text: `stage ${next.stage}` })
  for (const run of next.runs) {
    if (run.hung && !old.runs.find(r => r.role === run.role)?.hung) log.push({ at: now, who: run.role, text: `HUNG, silent ${span(run.idle * 1000)}` })
  }
  for (const task of next.tasks) {
    const was = old.tasks.find(t => t.id === task.id)
    if (was?.session !== task.session) log.push({ at: now, who: task.id, text: SESSION_NOTE[task.session] ?? 'running' })
  }

  return log
}

const tick = async ($: EngineInterface, cwd: string, isSlow: boolean) => {
  const agents = await $.agent.list()
  const board = isSlow ? await readBoard($, cwd) : undefined
  const main = isSlow ? await readMain($).catch(() => undefined) : undefined
  const now = Date.now()

  await update($, view, (old: View): View => {
    const seen = new Set(agents.map(a => a.id))
    const log: LogLine[] = pending.splice(0)
    const fresh: Row[] = agents.map(a => {
      const was = old.rows.find(r => r.id === a.id)
      const isLive = LIVE.has(a.status)
      const name = a.type.split(':').pop() || a.type
      if (!was && isLive) log.push({ at: now, who: name, text: 'started' })
      if (was && LIVE.has(was.status) && !isLive) log.push({ at: now, who: name, text: a.status })

      return {
        id: a.id,
        parentId: a.parentId,
        name,
        title: a.description || name,
        status: a.status,
        label: a.label.split('\n')[0] ?? '',
        tool: isLive ? (tools[a.id]?.text ?? '') : '',
        toolAt: tools[a.id]?.at ?? a.startTime,
        startTime: a.startTime,
        endedAt: isLive ? undefined : (was?.endedAt ?? now),
        tokens: a.tokenCount,
        usd: a.cost?.usd ?? 0,
      }
    })
    const gone: Row[] = old.rows
      .filter(r => !seen.has(r.id))
      .map(r => {
        if (LIVE.has(r.status)) log.push({ at: now, who: r.name, text: 'completed' })

        return { ...r, status: LIVE.has(r.status) ? 'completed' : r.status, tool: '', endedAt: r.endedAt ?? now }
      })
    if (board) log.push(...boardLog(old.board, board, now))

    return {
      now,
      board: board ?? old.board,
      rows: [...gone, ...fresh].sort((a, b) => a.startTime - b.startTime).slice(-30),
      main: main ?? old.main,
      lead: { ...lead },
      last,
      log: [...old.log, ...log].slice(-8),
    }
  })
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'team-panel', description: 'Show agent-team tasks and agents live in a pane' })
    void $.ui.open(OPEN)

    let count = 0
    let isBusy = false
    $.clock.every(1000, () => {
      if (isBusy) return
      isBusy = true
      void tick($, e.cwd, count++ % 3 === 0)
        .catch(() => undefined)
        .then(() => {
          isBusy = false
        })
    })

    return next(e)
  })

  on('command.run', { command: 'team-panel' }, async $ => {
    await $.ui.open(OPEN)

    return { text: 'Agent team pane opened.' }
  })

  on('tool.call', async ($, e, next) => {
    const detail = e.tool === 'Bash' ? `: ${e.command}` : ''
    const text = `${e.tool}${detail}`.replace(/\s+/g, ' ').slice(0, 80)
    if (e.agentId) {
      tools[e.agentId] = { text, at: Date.now() }
    } else {
      lead.tool = text
      lead.calls += 1
      if (EDITS.has(e.tool)) turn.edits += 1
      if (e.tool === 'Agent') turn.agents += 1
    }
    const ran = await next(e)
    if (!e.agentId && ran.isError === true) turn.errors += 1

    return ran
  })

  on('turn.start', async ($, e, next) => {
    if (e.agentId === undefined) {
      Object.assign(lead, { since: Date.now(), tool: '', calls: 0 })
      Object.assign(turn, NO_TURN)
      void spent($).then(usd => {
        turn.usdAt = usd
      })
    }

    return next(e)
  })

  on('turn.step', async function* ($, e, next) {
    if (e.agentId === undefined) {
      lead.requests += 1
      lead.effort = e.effort === undefined ? '' : String(e.effort)
    }

    return yield* next(e)
  })

  on('turn.complete', async ($, e, next) => {
    if (e.agentId === undefined && lead.since) {
      const ms = Date.now() - lead.since
      pending.push({ at: Date.now(), who: 'main', text: `turn ${clock(ms)} · ${lead.calls} tools` })
      lead.since = 0
      last = { ms, agents: turn.agents, edits: turn.edits, errors: turn.errors, usd: Math.max(0, (await spent($)) - turn.usdAt) }
    }

    return next(e)
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const v = await read($, view)
    const b = v.board
    const cols = Math.max(30, e.props.bodyColumns ?? 48)
    const inner = cols - 4
    const running = v.rows.filter(r => LIVE.has(r.status))
    const ids = new Set(v.rows.map(r => r.id))
    const stepsDone = b.steps.filter(s => s.state === 'done' || s.state === 'skip').length
    const barWidth = Math.max(6, inner - TITLE_WIDTH - 12)
    const first = Math.min(...v.rows.map(r => r.startTime), v.now)
    const whole = Math.max(1, v.now - first)
    const batchAgents = b.tasks.reduce((n, t) => n + t.agents.length, 0)
    const count = (session: string) => b.tasks.filter(t => t.session === session).length
    const hungRoles = new Set(b.runs.filter(r => r.hung).map(r => r.role))
    const hung = hungRoles.size + b.tasks.reduce((n, t) => n + t.agents.filter(a => a.hung).length, 0)
    const model = modelName(v.main.model) || 'Model'
    const effort = EFFORT[v.lead.effort] ?? 0
    const hasTask = b.task !== '' || b.stage !== ''
    const hasBatch = b.tasks.length > 0 || b.queue.length > 0
    const hasModules = b.modules.length > 0
    const isHungRow = (r: Row) => LIVE.has(r.status) && hungRoles.has(r.name)
    const agentsDone = v.rows.filter(r => !LIVE.has(r.status) && !BAD.has(r.status)).length
    const agentsBad = v.rows.filter(r => BAD.has(r.status) || isHungRow(r)).length
    const tasksAll = b.tasks.length + b.queue.length
    const modulesDone = b.modules.filter(m => m.state === 'DONE').length

    const rule = (color: string, fill: number) => {
      const strong = Math.max(0, Math.min(inner - 1, Math.round(fill * (inner - 1))))

      return (
        <Box flexDirection="row">
          <Text color={color}>●{'▬'.repeat(strong)}</Text>
          <Text color={color}>{'─'.repeat(inner - 1 - strong)}</Text>
        </Box>
      )
    }

    const sep = <Text dimColor>{'─'.repeat(cols)}</Text>

    const legend = (items: { color: string; mark: string; text: string; isDim?: boolean }[]) => (
      <Box flexDirection="row">
        {items.map(i => (
          <Box flexDirection="row">
            <Text color={i.color} dimColor={i.isDim === true}>
              {i.mark}{' '}
            </Text>
            <Text dimColor>{i.text}   </Text>
          </Box>
        ))}
      </Box>
    )

    const block = (color: string, name: string, status: string, label: string, value: string, fill: number | null, body: (JSX.Element | false)[]) => (
      <Box flexDirection="column" borderStyle="round" borderColor={color} paddingX={1}>
        <Box flexDirection="row" justifyContent="space-between">
          <Box flexDirection="row">
            <Text bold color={color}>
              {name}
            </Text>
            <Text bold color={color}>
              {' · '}
              {status}
            </Text>
          </Box>
          <Box flexDirection="row">
            <Text dimColor>{label} </Text>
            <Text color={color}>{value}</Text>
          </Box>
        </Box>
        {fill !== null && rule(color, fill)}
        {body}
      </Box>
    )

    return (
      <Box flexDirection="column">
        <Box flexDirection="column" alignItems="center">
          <Box flexDirection="row">
            <Text bold>AGENT TEAM · </Text>
            <Text bold color="claude">
              {model.toUpperCase()}
            </Text>
            <Text bold> {v.lead.since ? 'WORKING' : 'IDLE'}</Text>
            {hasTask && <Text bold> · </Text>}
            {hasTask && (
              <Text bold color="permission">
                TASK
              </Text>
            )}
            {hasTask && <Text bold> {b.stage || 'OPEN'}</Text>}
            {hasBatch && <Text bold> · </Text>}
            {hasBatch && (
              <Text bold color="suggestion">
                {b.tasks.length} TASKS
              </Text>
            )}
          </Box>
          {legend([
            { color: 'claude', mark: '■', text: 'main' },
            { color: 'suggestion', mark: '■', text: 'tasks' },
            { color: 'warning', mark: '■', text: 'module' },
            { color: 'permission', mark: '■', text: 'task' },
            { color: 'success', mark: '■', text: 'agents' },
            { color: 'inactive', mark: '■', text: 'log' },
          ])}
          {hung > 0 && (
            <Text bold color="error">
              ⚠ {hung} AGENT HUNG
            </Text>
          )}
        </Box>

        {block('claude', 'MAIN', v.lead.since ? `working ${clock(v.now - v.lead.since)}` : 'idle', 'ctx', `${v.main.percent}%`, null, [
          <Text dimColor>{model}</Text>,
          <Box flexDirection="row">
            <Text dimColor>effort </Text>
            <Text color="claude">{'▮'.repeat(effort) + '▯'.repeat(4 - effort)}</Text>
            <Text bold color="claude">
              {' '}
              {v.lead.effort || 'auto'}
            </Text>
            <Text dimColor>
              {'   '}
              {v.lead.requests} req
            </Text>
          </Box>,
          <Box flexDirection="row">
            <Text dimColor>ctx </Text>
            <Text color="claude">{meter(v.main.percent, 10)}</Text>
            <Text bold> {v.main.percent}%</Text>
            <Text dimColor>
              {' '}
              {short(v.main.tokens)}/{short(v.main.window)}
            </Text>
          </Box>,
          <Box flexDirection="row">
            <Text bold>${v.main.usd.toFixed(2)}</Text>
            {v.main.limits.map(l => {
              const left = l.resetsAt ? Date.parse(l.resetsAt) - v.now : NaN

              return (
                <Box flexDirection="row">
                  <Text dimColor>
                    {'  '}
                    {LIMIT_NAME[l.kind] ?? l.kind}{' '}
                  </Text>
                  <Text color="claude">{meter(l.percent, 5)}</Text>
                  <Text dimColor>
                    {' '}
                    {Math.round(l.percent)}%{Number.isFinite(left) ? ` ↻${span(left)}` : ''}
                  </Text>
                </Box>
              )
            })}
          </Box>,
          v.lead.since > 0 && (
            <Text color="claude" wrap="truncate-end">
              » {v.lead.tool || 'thinking'} · {v.lead.calls} tools
            </Text>
          ),
        ])}

        {hasBatch && sep}
        {hasBatch &&
          block('suggestion', 'TASKS', `${count('run')} running`, 'agents', String(batchAgents), count('done') / Math.max(1, tasksAll), [
            legend([
              { color: 'suggestion', mark: '▬', text: `${count('done')} done` },
              { color: 'suggestion', mark: '●', text: `${count('run')} running` },
              { color: 'warning', mark: '⏸', text: `${count('ask')} waiting` },
              { color: 'suggestion', mark: '─', text: `${b.queue.length} queued` },
            ]),
            ...b.tasks.map(t => (
              <Box flexDirection="column">
                <Text bold={t.session === 'run'} color={t.session === 'ask' ? 'warning' : t.session === 'run' ? 'suggestion' : undefined} dimColor={t.session === 'done' || t.session === 'none'} wrap="truncate-end">
                  {SESSION[t.session] ?? '■'} {t.id} {t.stage || '--'} · {t.steps} steps
                  {SESSION_NOTE[t.session] ? ` · ${SESSION_NOTE[t.session]}` : ''}
                </Text>
                {t.agents.map(a => (
                  <Text color={a.hung ? 'error' : undefined} dimColor={!a.hung} wrap="truncate-end">
                    {'   '}
                    {a.hung ? `⚠ ${a.role} silent ${span(a.idle * 1000)}` : `${a.role} · ${a.tool || 'starting'}`}
                  </Text>
                ))}
              </Box>
            )),
            ...b.queue.map(id => <Text dimColor>○ {id} queued</Text>),
          ])}

        {hasModules && sep}
        {hasModules &&
          block('warning', 'MODULES', `${b.modules.filter(m => m.running > 0).length} running`, 'done', `${modulesDone}/${b.modules.length}`, null, [
            ...b.modules.map(m => {
              const isDone = m.state === 'DONE'
              const filled = Math.round((m.done / Math.max(1, m.total)) * 10)

              return (
                <Box flexDirection="row">
                  <Text color={isDone ? 'success' : 'warning'}>{isDone ? '✓' : m.running > 0 ? '▶' : '○'} </Text>
                  <Text bold={m.running > 0} dimColor={isDone} wrap="truncate-end">
                    {`${m.module} ${m.title}`.slice(0, TITLE_WIDTH + 3).padEnd(TITLE_WIDTH + 3)}{' '}
                  </Text>
                  <Text color="warning">{'━'.repeat(filled)}</Text>
                  <Text color="warning">{'─'.repeat(10 - filled)}</Text>
                  <Text dimColor>
                    {' '}
                    {m.done}/{m.total}
                  </Text>
                </Box>
              )
            }),
          ])}

        {hasTask && sep}
        {hasTask &&
          block('permission', 'TASK', `${b.task || 'none'}${b.stage ? ` ${b.stage.toLowerCase()}` : ''}`, 'steps', `${stepsDone}/${b.steps.length}`, stepsDone / Math.max(1, b.steps.length), [
            b.steps.length === 0 && <Text dimColor>No steps on the board.</Text>,
            ...b.steps.map(s => (
              <Text dimColor={s.state !== 'doing'} bold={s.state === 'doing'} color={s.state === 'doing' ? 'permission' : undefined} wrap="truncate-end">
                {MARK[s.state] ?? '○'} {s.n}. {s.title}
                {s.role ? ` @${s.role}` : ''}
              </Text>
            )),
            b.debate.run !== '' && (
              <Text color={b.debate.whys > 0 ? 'warning' : 'permission'} wrap="truncate-end">
                » debate {b.debate.run} · {b.debate.posts} posts · {b.debate.whys} WHY open · {b.debate.votes} votes
              </Text>
            ),
          ])}

        {sep}
        {block('success', 'AGENTS', `${running.length} running`, 'total', String(v.rows.length), agentsDone / Math.max(1, v.rows.length), [
          legend([
            { color: 'success', mark: '▬', text: `${agentsDone} done` },
            { color: 'success', mark: '●', text: `${running.length - v.rows.filter(isHungRow).length} running` },
            { color: 'error', mark: '✗', text: `${agentsBad} failed` },
          ]),
          <Text wrap="truncate-end">
            tok: {short(v.rows.reduce((n, r) => n + r.tokens, 0))}  cost: ${v.rows.reduce((n, r) => n + r.usd, 0).toFixed(2)}  turn: {clock(v.last.ms)}  edits: {v.last.edits}  errors:{' '}
            {v.last.errors}
          </Text>,
          v.rows.length === 0 && <Text dimColor>No agents yet.</Text>,
          ...v.rows.map((r, i) => {
            const isLive = LIVE.has(r.status)
            const isBad = BAD.has(r.status)
            const run = b.runs.find(x => x.role === r.name)
            const isHung = isHungRow(r)
            const label = `${r.parentId && ids.has(r.parentId) ? '└' : ''}${i + 1}: ${r.title}`
            const from = Math.min(barWidth - 1, Math.floor(((r.startTime - first) / whole) * barWidth))
            const to = Math.max(from + 1, Math.min(barWidth, Math.ceil((((r.endedAt ?? v.now) - first) / whole) * barWidth)))
            const tone = isBad || isHung ? 'error' : 'success'
            const cost = `${short(r.tokens)} tok · $${r.usd.toFixed(2)}`
            const quiet = v.now - r.toolAt >= 60000 ? ` · last tool ${span(v.now - r.toolAt)} ago` : ''
            const result = run?.state === 'DONE' && run.result ? run.result : ''
            const detail = isHung
              ? `${r.name} · HUNG, silent ${span((run?.idle ?? 0) * 1000)} · ${run?.tool ?? ''}`
              : isLive
                ? `${r.name} · ${r.status} · ${cost} · ${r.tool || r.label}${quiet}`
                : result
                  ? `${r.name} · ${cost} · ${result}`
                  : ''

            return (
              <Box flexDirection="column">
                <Box flexDirection="row">
                  <Text color={tone}>{isHung ? '⚠' : isBad ? '✗' : isLive ? '▶' : '✓'} </Text>
                  <Text bold={isLive} dimColor={!isLive && !isBad}>
                    {label.slice(0, TITLE_WIDTH + 3).padEnd(TITLE_WIDTH + 3)}{' '}
                  </Text>
                  <Text color={tone}>{'·'.repeat(from)}</Text>
                  <Text color={tone}>{'━'.repeat(to - from)}</Text>
                  <Text color={tone}>{'·'.repeat(barWidth - to)}</Text>
                  <Text dimColor={!isLive}> {clock((r.endedAt ?? v.now) - r.startTime).padStart(5)}</Text>
                </Box>
                {detail !== '' && (
                  <Text color={isHung ? 'error' : undefined} dimColor={!isHung} wrap="truncate-end">
                    {'  '}
                    {detail}
                  </Text>
                )}
              </Box>
            )
          }),
          <Text color="success" wrap="truncate-end">
            » last turn {clock(v.last.ms)} · {v.last.agents} agents · +${v.last.usd.toFixed(2)}
          </Text>,
        ])}

        {sep}
        {block('inactive', 'SESSION', 'log', 'events', String(v.log.length), v.log.length / 8, [
          v.log.length === 0 && <Text dimColor>Nothing yet.</Text>,
          ...v.log.map(l => (
            <Box flexDirection="row">
              <Text dimColor>{timeOfDay(l.at)} </Text>
              <Text bold color="permission">
                {l.who.slice(0, NAME_WIDTH).padEnd(NAME_WIDTH)}
              </Text>
              <Text dimColor wrap="truncate-end">
                {' '}
                {l.text}
              </Text>
            </Box>
          )),
        ])}
      </Box>
    )
  })
}
