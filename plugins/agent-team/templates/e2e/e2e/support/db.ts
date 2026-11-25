import { execFileSync } from 'node:child_process';
import { resetCmd } from '../project';

export function inApp(cmd: string): string {
  const exec = process.env.APP_EXEC;
  if (!exec) throw new Error('APP_EXEC trống: chạy qua .claude/agent-team/agent-db.sh e2e <task-id>');
  return execFileSync('sh', ['-c', `${exec} ${cmd}`], { encoding: 'utf8' });
}

export const reset = (...args: (string | number)[]) => inApp([resetCmd, ...args].join(' '));
