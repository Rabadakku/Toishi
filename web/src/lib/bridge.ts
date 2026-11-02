/**
 * Typed access to the Python bridge. In the app this is pywebview's js_api
 * (app/api.py); in a plain browser it is the mock in mock-bridge.ts.
 */
import type {
  AnswerPreview,
  AttemptResult,
  BackupList,
  CardMedia,
  CardMediaRequest,
  Diagnosis,
  DiagnoseRequest,
  FlagRequest,
  FlagResult,
  FlashcardRequest,
  Forecast,
  GiveUpRequest,
  HintReveal,
  ItemRequest,
  Library,
  LibraryStateRequest,
  Preferences,
  ProfileState,
  ReadAnswerRequest,
  StartRequest,
  SubmitRequest,
  Summary,
  Tick,
  TickRequest,
  TodayView,
  Turn,
} from './types';

export interface AppInfo {
  name: string;
  version: string;
  python: string;
  self_test: boolean;
}

export interface SelfTestCheck {
  name: string;
  ok: boolean;
  detail: string;
}

export interface SelfTestReport {
  ok: boolean;
  checks: SelfTestCheck[];
  page_ms: number;
}

/**
 * Mirrors the public methods of app.api.Api, name for name (tests/test_app.py checks).
 * Every method takes at most one JSON object: pywebview passes arguments positionally.
 * A call the session can't act on rejects with an Error named "UserMessage" (see
 * userMessage below); its text is for the student.
 */
export interface BridgeApi {
  ping(message: string): Promise<string>;
  version(): Promise<string>;
  app_info(): Promise<AppInfo>;
  report_self_test(report: SelfTestReport): Promise<null>;

  profile_get(): Promise<ProfileState>;
  profile_create(request: { name: string }): Promise<ProfileState>;
  prefs_get(): Promise<Preferences>;
  prefs_set(preferences: Preferences): Promise<null>;

  /** The verified backups of the profile that failed to open (or the open one), newest first. */
  restore_list(): Promise<BackupList>;
  /** Swap in a backup (the current file is kept) and open the profile again. */
  restore_backup(request: { id: string }): Promise<ProfileState>;
  /** Check the profile that failed to open again; opens it if it now passes. */
  restore_recheck(): Promise<ProfileState>;

  library_get(): Promise<Library>;
  library_set_state(request: LibraryStateRequest): Promise<Library>;
  /** The media a card shows, as URLs on this origin (images, sounds, an imported deck's CSS). */
  library_card_media(request: CardMediaRequest): Promise<CardMedia>;

  /** Home: today's problems and minutes per course, exams. */
  study_today(): Promise<TodayView>;
  study_forecast(): Promise<Forecast>;
  /** Begin a session, or resume today's open one at the same problem (QUE-16). */
  study_start(request: StartRequest): Promise<Turn>;
  study_resume(): Promise<Turn | null>;
  study_current(): Promise<Turn>;
  /** Parse what the student typed and say how it was read. Never an attempt. */
  study_read_answer(request: ReadAnswerRequest): Promise<AnswerPreview>;
  /** Grade the answer on screen (AGENTS.md rule 5: committed when graded). */
  study_submit(request: SubmitRequest): Promise<AttemptResult>;
  study_give_up(request: GiveUpRequest): Promise<AttemptResult>;
  /** Self-graded problems: the solution (and rubric) before grading; nothing is graded. */
  study_show_solution(request: ItemRequest): Promise<AttemptResult>;
  /** Next hint on the ladder, one per call. */
  study_hint(request: ItemRequest): Promise<HintReveal>;
  /** Save the active time and draft (QUE-16); says when a break is due. */
  study_tick(request: TickRequest): Promise<Tick>;
  /** Record the "What went wrong?" pick (grades the miss with it). */
  study_diagnose(request: DiagnoseRequest): Promise<Diagnosis>;
  /** Space: continue to the next item, or the summary. */
  study_next(request: ItemRequest): Promise<Turn>;
  /** "Too easy" (E), "I was right" (D), "Report problem" (R). */
  study_flag(request: FlagRequest): Promise<FlagResult>;
  /** Undo the last answer (U, Edit > Undo Last Answer): the problem comes back. */
  study_undo(): Promise<Turn>;
  /** Lighter set on or off for the rest of today's session (QUE-10). */
  study_set_lighter(request: { on: boolean }): Promise<Turn>;
  study_rate_flashcard(request: FlashcardRequest): Promise<AttemptResult>;
  /** End the session now: the summary with tomorrow's forecast. */
  study_end(): Promise<Summary>;
}

declare global {
  interface Window {
    pywebview?: { api: BridgeApi };
  }
}

function currentApi(): BridgeApi | undefined {
  const api = window.pywebview?.api;
  // pywebview creates `api` as an empty object first and adds the methods later.
  return api && typeof api.ping === 'function' ? api : undefined;
}

/** Resolve once the bridge is usable (pywebview fires `pywebviewready`). */
export function waitForBridge(timeoutMs = 10_000): Promise<BridgeApi> {
  const ready = currentApi();
  if (ready) return Promise.resolve(ready);
  return new Promise((resolve, reject) => {
    const onReady = (): void => {
      const api = currentApi();
      if (!api) return;
      window.clearTimeout(timer);
      window.removeEventListener('pywebviewready', onReady);
      resolve(api);
    };
    const timer = window.setTimeout(() => {
      window.removeEventListener('pywebviewready', onReady);
      reject(new Error(`Python bridge not available after ${timeoutMs} ms`));
    }, timeoutMs);
    window.addEventListener('pywebviewready', onReady);
  });
}

/** The student-facing text of a refused call (Python raised UserMessage), else null. */
export function userMessage(error: unknown): string | null {
  return error instanceof Error && error.name === 'UserMessage' ? error.message : null;
}
