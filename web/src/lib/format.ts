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

const ISO_DAY = /^(\d{4})-(\d{2})-(\d{2})$/;

/** A YYYY-MM-DD study day as a local date (never through UTC, which can shift the day). */
export function parseDay(day: string): Date | null {
  const match = ISO_DAY.exec(day);
  if (!match) return null;
  const date = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  return Number.isNaN(date.getTime()) ? null : date;
}

/** The local calendar day of a date, as YYYY-MM-DD. */
export function localDay(date: Date = new Date()): string {
  const pad = (n: number): string => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

/** The day `days` after a YYYY-MM-DD day (negative for before). */
export function addDays(day: string, days: number): string {
  const date = parseDay(day) ?? new Date();
  date.setDate(date.getDate() + days);
  return localDay(date);
}

function dateText(date: Date): string {
  const sameYear = date.getFullYear() === new Date().getFullYear();
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    ...(sameYear ? {} : { year: 'numeric' }),
  }).format(date);
}

/** "Nov 7" for a YYYY-MM-DD day ("Nov 7, 2027" in another year); the text itself if unreadable. */
export function formatDay(day: string): string {
  const date = parseDay(day);
  return date ? dateText(date) : day;
}

/** "Nov 7" for an epoch-ms moment. */
export function formatMoment(ms: number): string {
  return dateText(new Date(ms));
}

/** "93%" for 0.93. */
export function formatPercent(fraction: number): string {
  return `${Math.round(fraction * 100)}%`;
}

/** A number with at most `digits` significant digits, without trailing zeros ("0.693", "2"). */
export function formatNumber(value: number, digits = 3): string {
  if (!Number.isFinite(value)) return String(value);
  if (value === 0) return '0';
  return String(Number(value.toPrecision(digits)));
}
