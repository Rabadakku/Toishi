/**
 * The active-time clock (TIME-1 to TIME-3). It counts only while nothing has paused it.
 * Several reasons can hold it paused at once; it runs again when the last one lifts.
 *
 *  manual  the student pressed Pause (button, Esc or P)
 *  focus   the window lost focus, the app was hidden, the screen locked or the Mac slept
 *  idle    the "Still working?" note went unanswered; time is trimmed back to the note
 *
 * It never pauses for keyboard or mouse inactivity by itself, because the work happens on paper.
 */
export type PauseReason = 'manual' | 'focus' | 'idle';

export class ActiveClock {
  private bankedMs = 0;
  private runningSince: number | null = null;
  private pausedSince: number | null = null;
  private readonly reasons = new Set<PauseReason>();
  /** Total paused time since the last reset. */
  pausedMs = 0;
  longestPauseMs = 0;
  /** How many times the clock went from running to paused. */
  pauseCount = 0;
  idleTrimmed = false;

  constructor(private readonly now: () => number = () => performance.now()) {}

  /** Start the clock from `startMs` (active time already counted, after a resume). */
  reset(startMs = 0): void {
    this.bankedMs = Math.max(0, startMs);
    this.pausedMs = 0;
    this.longestPauseMs = 0;
    this.pauseCount = 0;
    this.idleTrimmed = false;
    this.reasons.clear();
    this.pausedSince = null;
    this.runningSince = this.now();
  }

  /** Stop counting for good (the problem is finished). */
  stop(): void {
    this.bankedMs = this.elapsedMs();
    this.runningSince = null;
    this.reasons.clear();
    this.pausedSince = null;
  }

  elapsedMs(): number {
    return this.bankedMs + (this.runningSince === null ? 0 : this.now() - this.runningSince);
  }

  isPaused(reason?: PauseReason): boolean {
    return reason ? this.reasons.has(reason) : this.reasons.size > 0;
  }

  pause(reason: PauseReason): void {
    if (this.reasons.has(reason)) return;
    if (this.reasons.size === 0 && this.runningSince !== null) {
      this.bankedMs = this.elapsedMs();
      this.runningSince = null;
      this.pausedSince = this.now();
      this.pauseCount += 1;
    }
    this.reasons.add(reason);
  }

  resume(reason: PauseReason): void {
    if (!this.reasons.delete(reason) || this.reasons.size > 0) return;
    const at = this.now();
    if (this.pausedSince !== null) {
      const length = at - this.pausedSince;
      this.pausedMs += length;
      this.longestPauseMs = Math.max(this.longestPauseMs, length);
    }
    this.pausedSince = null;
    this.runningSince = at;
  }

  /** The "Still working?" note timed out: forget the time since `ms`, then hold the clock. */
  trimBackTo(ms: number): void {
    this.bankedMs = Math.min(this.elapsedMs(), ms);
    this.runningSince = null;
    this.idleTrimmed = true;
    if (this.reasons.size === 0) this.pausedSince = this.now();
    this.reasons.add('idle');
  }
}

/** Idle threshold for the "Still working?" note: 3 times the target, at least 5 minutes. */
export function idleThresholdMs(targetMs: number | null): number {
  return Math.max(3 * (targetMs ?? 0), 5 * 60 * 1000);
}

/**
 * Notices the Mac waking from sleep: the wall clock jumps while the page's monotonic clock
 * (which stops during sleep in WebKit) does not. The first attempt after a wake is left out
 * of speed baselines (TIME-5).
 */
export class WakeWatch {
  private lastWall = Date.now();
  private lastMono = performance.now();
  private timer: number | undefined;

  constructor(private readonly onWake: () => void, private readonly gapMs = 30_000) {}

  start(): void {
    this.stop();
    this.lastWall = Date.now();
    this.lastMono = performance.now();
    this.timer = window.setInterval(() => this.check(), 5_000);
  }

  stop(): void {
    window.clearInterval(this.timer);
  }

  check(): void {
    const wall = Date.now();
    const mono = performance.now();
    if (wall - this.lastWall - (mono - this.lastMono) > this.gapMs) this.onWake();
    this.lastWall = wall;
    this.lastMono = mono;
  }
}

/** Time the "Still working?" note waits for an answer before pausing the clock. */
export const STILL_WORKING_GRACE_MS = 60_000;
