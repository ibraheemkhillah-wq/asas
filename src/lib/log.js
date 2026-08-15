const levels = { debug: 10, info: 20, warn: 30, error: 40 };
const threshold = levels[process.env.LOG_LEVEL || 'info'] ?? 20;

function emit(level, msg, extra) {
  if (levels[level] < threshold) return;
  const line = `${new Date().toISOString()} [${level.toUpperCase()}] ${msg}`;
  const out = level === 'error' || level === 'warn' ? console.error : console.log;
  if (extra !== undefined) out(line, extra);
  else out(line);
}

export const log = {
  debug: (m, e) => emit('debug', m, e),
  info: (m, e) => emit('info', m, e),
  warn: (m, e) => emit('warn', m, e),
  error: (m, e) => emit('error', m, e),
};
