export type Row = {
  id: string
  parentId?: string
  name: string
  title: string
  status: string
  label: string
  tool: string
  toolAt: number
  startTime: number
  endedAt?: number
  tokens: number
  usd: number
}

export type Step = { n: string; state: string; title: string; role: string }

export type Run = { role: string; state: string; tool: string; idle: number; hung: boolean; result: string }

export type Debate = { run: string; posts: number; whys: number; votes: number }

export type BatchTask = { id: string; stage: string; session: string; steps: string; agents: Run[] }

export type Module = { module: string; title: string; state: string; done: number; total: number; running: number }

export type Board = {
  stage: string
  task: string
  steps: Step[]
  runs: Run[]
  debate: Debate
  tasks: BatchTask[]
  queue: string[]
  modules: Module[]
}

export type Limit = { kind: string; percent: number; resetsAt?: string }

export type Main = { model: string; percent: number; tokens: number; window: number; usd: number; limits: Limit[] }

export type Lead = { since: number; tool: string; calls: number; requests: number; effort: string }

export type Turn = { ms: number; agents: number; edits: number; errors: number; usd: number }

export type LogLine = { at: number; who: string; text: string }

export type View = { now: number; board: Board; rows: Row[]; main: Main; lead: Lead; last: Turn; log: LogLine[] }

declare module 'claude-code' {
  interface PluginState {
    'agent-team': { view: Shaped<View> }
  }
}
