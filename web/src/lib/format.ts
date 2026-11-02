/** "3:40" for 220 seconds. Minutes are not capped, so an hour reads "60:00". */
export function formatDuration(totalSeconds: number): string {
  const seconds = Math.max(0, Math.round(totalSeconds));
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`;
}

/** "3:40 · target 4:00", or just "3:40" while the skill has no target yet. */
export function formatTimeWithTarget(activeSeconds: number, targetSeconds: number | null): string {
  const active = formatDuration(activeSeconds);
  return targetSeconds === null ? active : `${active} · target ${formatDuration(targetSeconds)}`;
}

/** "3:40" for 220 000 ms. */
export function formatMs(ms: number): string {
  return formatDuration(ms / 1000);
}
