/**
 * Payload types of the Python bridge (app/api.py), the contract between this page and
 * Python. The study payloads mirror core/queue/views.py field for field: app/api.py returns
 * `core.queue.to_dict` of the StudyService views unchanged.
 *
 * Rules both sides follow:
 * - JSON only; field names are snake_case (they are Python dict keys).
 * - Every time is milliseconds (`*_ms`); the page formats them.
 * - The item on screen is named by its `item_key` (a plan item), never by a card id.
 * - Text fields ending in `_md` use the card format's Markdown with `\( \)` and `\[ \]`
 *   math, images and tables. The page renders them through KaTeX, never as raw HTML.
 * - Nothing shown before an answer names the problem's skill (Study screen 7): skill names
 *   appear only in the solution, the summary, the library and the Skills screen. The
 *   textbook section is shown under the problem (wave 2 learning design), except in a
 *   closed-book sitting.
 * - The wave 2 planner payloads (roles, sittings, course settings, skills, the student
 *   model) follow docs/design/wave2-integration.md section 6.
 */

// ---------------------------------------------------------------------------
// The item on screen (core.queue.views.ProblemView)
// ---------------------------------------------------------------------------

/** How an answer is entered and checked (card-format: Answer types). */
export type AnswerType =
  | 'number'
  | 'expression'
  | 'equation'
  | 'antiderivative'
  | 'set'
  | 'list'
  | 'interval'
  | 'point'
  | 'vector'
  | 'matrix'
  | 'choice'
  | 'truefalse'
  | 'text'
  | 'quantity'
  | 'self';

/** What the card is. */
export type CardKind = 'problem' | 'example' | 'flashcard' | 'cloze' | 'find-error' | 'method';

/** What the session item is: problems are graded; examples are read; flashcards are rated. */
export type ItemKind = 'problem' | 'example' | 'flashcard';

/** Why the item is here (spec: Reason tags). Flashcards use 'review' with label "Flashcard". */
export type ReasonTag = 'review' | 'relearn' | 'new-skill' | 'check' | 'exam-prep' | 'redo' | 'stretch';

/** The small tag at the top of the study screen and the text behind "Why is this here?". */
export interface Reason {
  tag: ReasonTag;
  /** "Review", "Check", "New skill": a word or two, no section names. */
  label: string;
  /** The "Why is this here?" sentence (plain text). */
  why: string;
}

/** One option of a choice answer; it is answered by its 1-based number. */
export interface ChoiceView {
  /** 0-based position. */
  index: number;
  text_md: string;
}

/** One answer box. A single-box card has one part with `label` null. */
export interface PartView {
  label: string | null;
  prompt_md: string | null;
  answer_type: AnswerType;
  choices: ChoiceView[];
  /** A choice box with several right options: select all that apply. */
  multiple?: boolean;
}

/** The card behind the item. */
export interface CardView {
  id: string;
  rev: number;
  kind: CardKind;
  /** The question (or a flashcard's front, a cloze card's text). */
  prompt_md: string;
  parts: PartView[];
  calculator: boolean;
  /** 'radians' unless the card says 'degrees'. */
  angles: string;
  plot: string | null;
  /** The student grades it against the solution (answer-type self). */
  self_graded: boolean;
  /** A flashcard's back. */
  back_md: string | null;
  /** A worked example's solution (examples show it at once). */
  solution_md: string | null;
  /** Find-the-error: another student's numbered steps (no skill names). */
  shown_work: StepView[];
  /** Find-the-error: why the step is wrong, three or four options, one right. */
  reasons: ChoiceView[];
  /** Find-the-error, highlighted version: the wrong step is given ("Step 3 is wrong. Why?"). */
  error_step: number | null;
  /** Cloze: the blank asked (c1 is 1). The front and back come rendered. */
  cloze: number | null;
  /** A flashcard with an answer: the student types it and it is graded automatically. */
  type_answer: boolean;
}

/** What the planner has an item work on (core.plan Role). Flashcards have none. */
export type Role = 'new' | 'growth' | 'maintenance' | 'check' | 'practice-test' | 'focused' | 'sitting';

/** A skill's milestones: M1 (tier 2), M2 (tier 3 at pace), M3 (the target tier at pace), Keep. */
export type MilestoneName = 'M1' | 'M2' | 'M3' | 'keep';

/** Where the problem's section is in the textbook: "OpenStax Calculus Volume 1", "4.1". */
export interface Textbook {
  book: string;
  section: string;
}

/**
 * An item of a closed-book, timed sitting. Design v1.3: the time limit belongs to the item's
 * skill block (that skill's problems in the sitting), like a block of an exam.
 */
export interface SittingView {
  id: string;
  /** 1-based place in the whole sitting: "problem 2 of 5". */
  index: number;
  total: number;
  /**
   * The limit of the item's skill block: the sum of the standard times of that skill's
   * problems in the sitting. Shown, never enforced: nothing is cut off at the limit.
   */
  time_limit_ms: number;
  /** Active time already spent on the block's earlier problems; the page adds this item's running time. */
  block_elapsed_ms: number;
}

/** The item on screen (Turn.problem). */
export interface ProblemView {
  item_key: string;
  kind: ItemKind;
  card: CardView;
  /** The tag at the top and its "Why is this here?" sentence. */
  reason: Reason;
  attempts_allowed: number;
  tries_used: number;
  /** What was typed before a quit or reload (study_tick), opaque to Python. */
  draft: string | null;
  /** Active time already counted for this item (a resumed problem continues from it). */
  active_ms: number;
  /** Null while answering: the target shows only after submitting. */
  target_ms: number | null;
  untimed: boolean;
  practice_test: boolean;
  /** The planner's role for the item; null for flashcards. */
  role: Role | null;
  /**
   * The planner's reason code ('ladder:smaller', 'ladder:prerequisite', 'band' ...). Section 6
   * called it `reason`, which the tag above already is; agreed with W1 as `plan_reason`.
   */
  plan_reason: string | null;
  /** The textbook section, from the section's deck and the pack's source. */
  textbook: Textbook | null;
  /** Set on the items of a closed-book sitting. */
  sitting: SittingView | null;
}

/** "7 of 20" and the running tally. */
export interface Progress {
  position: number;
  total: number;
  answered: number;
  correct: number;
}

// ---------------------------------------------------------------------------
// Answering (requests)
// ---------------------------------------------------------------------------

/** 'mathlive' for LaTeX from the math field, 'text' for plain-text mode and choices. */
export type AnswerSource = 'text' | 'mathlive';

/** What the student entered in one box. Choices are their 1-based numbers ("1, 3"). */
export interface PartAnswer {
  part: string | null;
  value: string;
  source: AnswerSource;
}

/** What the page measured (TIME-1 to TIME-5). Python bounds it by the wall clock. */
export interface TimingReport {
  /** All active time on this item so far (pauses excluded), including a resumed part. */
  active_ms: number;
  /** This attempt: shown (or retried) until the first keystroke in an answer box. */
  solve_ms: number | null;
  /** This attempt: first keystroke until submit. */
  entry_ms: number | null;
  paused_ms: number;
  pause_count: number;
  longest_pause_ms: number;
  /** The Mac slept during the attempt (left out of speed baselines, TIME-5). */
  after_wake: boolean;
  /** The "Still working?" note timed out and the time was trimmed back (TIME-3). */
  idle_trimmed: boolean;
}

/** Enter submits "sure"; Shift+Enter submits "unsure". */
export type Confidence = 'sure' | 'unsure';

/** Self-grading: matched the solution, a minor slip, or didn't get it. */
export type SelfGrade = 'matched' | 'minor-slip' | 'missed';

/** study_submit. `item_key` guards against a stale page. */
export interface SubmitRequest {
  item_key: string;
  answers: PartAnswer[];
  confidence: Confidence;
  guessed?: boolean;
  self_grade?: SelfGrade | null;
  /** Self-graded with a rubric: how many of its steps the student's work matched. */
  rubric_ticked?: number | null;
  /** Find-the-error: the step picked as wrong (not needed when it is highlighted). */
  error_step?: number | null;
  /** Find-the-error: the index of the reason picked. */
  reason?: number | null;
  timing: TimingReport;
}

/** study_give_up. */
export interface GiveUpRequest {
  item_key: string;
  timing: TimingReport;
}

/** study_read_answer: the live preview of one box. */
export interface ReadAnswerRequest {
  item_key: string;
  part: string | null;
  value: string;
  source: AnswerSource;
}

/** The "We read your answer as ..." preview (core.grader.Preview). */
export interface AnswerPreview {
  /** Parsed and the right shape. False with a message: a syntax or shape error. */
  ok: boolean;
  /** The parsed answer as LaTeX with multiplication made explicit. */
  read_as_latex: string | null;
  message: string;
  /** Reading notes ("Read sinx as sin(x)"). */
  hints: string[];
}

/** A request about the item on screen (next, show solution ...). */
export interface ItemRequest {
  item_key: string;
}

/** Buttons after grading: E too easy, D dispute ("I was right"), R report. */
export type FlagKind = 'too_easy' | 'dispute' | 'report' | 'flag' | 'suspend';

/** study_flag. */
export interface FlagRequest {
  item_key: string;
  kind: FlagKind;
  note?: string | null;
}

/** study_rate_flashcard: a rating 1-4 (Again, Hard, Good, Easy) or a typed answer. */
export interface FlashcardRequest {
  item_key: string;
  rating?: 1 | 2 | 3 | 4 | null;
  answer?: string | null;
  source?: AnswerSource;
  timing?: TimingReport;
}

/** study_tick: the active time so far and the typed draft, saved for a resume (QUE-16). */
export interface TickRequest {
  item_key: string;
  active_ms: number;
  draft: string | null;
}

/** study_start: begin today's session (or resume it), or another kind of session. */
export interface StartRequest {
  /** The focused, weak-spot and lighter modes went with the old engine (wave 2 section 4). */
  mode?: 'daily' | 'extra' | 'practice-test';
  /** An Untimed session (TIME-6); null: the profile's default. */
  untimed?: boolean | null;
  count?: number | null;
  section_id?: string | null;
  skill_id?: string | null;
  weak_spots?: boolean;
  exam_id?: number | null;
  timed?: boolean;
}

// ---------------------------------------------------------------------------
// Results
// ---------------------------------------------------------------------------

/** One box's verdict. 'invalid' (syntax or shape) never counts as an attempt. */
export type VerdictStatus = 'correct' | 'incorrect' | 'invalid' | 'undecidable' | 'unsupported';

/** The verdict for one box. */
export interface PartVerdictView {
  part: string | null;
  status: VerdictStatus;
  /** LaTeX: the answer as read. */
  read_as: string | null;
  /** The checker's message (an invalid answer's reason). */
  message: string;
  /**
   * A known wrong answer matched: its feedback (Markdown). Only results that carry the
   * solution have it; a retry result ("Not quite") carries no feedback and no wrong_step.
   */
  feedback: string | null;
  /** ... and the solution step it comes from (@step). */
  wrong_step?: number | null;
  /** This box is settled (right, or out of tries); it is not checked again. */
  final: boolean;
  tries_used: number;
}

/** One numbered, skill-tagged step of a worked solution (Step 0 is set-up). */
export interface StepView {
  number: number;
  skill_id: string | null;
  skill_name: string | null;
  label: string;
  body_md: string;
}

/** Everything shown once an item is finished. */
export interface SolutionView {
  skill_id: string | null;
  skill_name: string | null;
  /** The correct answer. */
  answer_md: string | null;
  /** A solution without numbered steps. */
  solution_md: string | null;
  steps: StepView[];
  alternative_md: string | null;
  active_ms: number | null;
  target_ms: number | null;
  /** "3:40 · target 4:00"; null in Untimed sessions. */
  time_text: string | null;
  /** Missed while marked "sure". */
  confident_error: boolean;
  /** Offer "Too easy" (a clean first-try success). */
  can_mark_too_easy: boolean;
  textbook_ref: string | null;
  /** Self-graded: the checklist to tick. */
  rubric: string[];
  /** Find-the-error: the shown work, set beside the correct solution. */
  shown_work: StepView[];
}

/** How a find-the-error answer went: the step, the reason and the corrected value. */
export interface FindErrorView {
  error_step: number | null;
  /** Index of the right reason. */
  right_reason: number | null;
  step_ok: boolean;
  reason_ok: boolean;
  value_ok: boolean;
}

/**
 * retry: "Not quite", try again or give up. invalid: fix the form (not an attempt). correct /
 * incorrect: finished, `solution` set (a give-up is incorrect). self-grade: the checker
 * can't decide; the student grades against `solution`. recorded: a flashcard or
 * practice-test answer was saved.
 */
export type Outcome = 'retry' | 'correct' | 'incorrect' | 'invalid' | 'self-grade' | 'recorded';

/** The result of study_submit, study_give_up and study_rate_flashcard. */
export interface AttemptResult {
  item_key: string;
  outcome: Outcome;
  verdicts: PartVerdictView[];
  message: string;
  solution: SolutionView | null;
  tries_used: number;
  attempts_allowed: number;
  /** Flashcards: the rating recorded (1-4). */
  rating: number | null;
  /** A break reminder is due (50 minutes of active time by default). */
  break_due: boolean;
  find_error: FindErrorView | null;
  /** After "Not quite": the item stays open for another try. Problems allow any number. */
  can_retry: boolean;
  /** This answer was the item's first try, the one that counts; later tries are practice. */
  first_try_counted: boolean;
}

/** The outcome of a flag. */
export interface FlagResult {
  ok: boolean;
  message: string;
  /** False when the attempt no longer counts (dispute, report). */
  attempt_counts: boolean;
}

/** study_tick's answer. */
export interface Tick {
  saved: boolean;
  active_ms: number;
  break_due: boolean;
}

// ---------------------------------------------------------------------------
// Home, forecast and the summary
// ---------------------------------------------------------------------------

/** One course's share of a day. */
export interface CourseLine {
  course_id: string;
  title: string;
  problems: number;
  minutes: number;
}

/** A day's problems and minutes (tomorrow on the summary). */
export interface Forecast {
  day: string;
  problems: number;
  minutes: number;
  courses: CourseLine[];
}

/** An exam countdown; `practice_test` once it is within 21 days. */
export interface ExamLine {
  exam_id: number | null;
  name: string;
  course_id: string | null;
  days_left: number;
  practice_test: boolean;
}

/** Where a weekly-hours figure comes from: the student's own history, the course standard, none. */
export type HoursBasis = 'history' | 'standard' | 'none';

/** A closed-book sitting planned today and the skills it certifies (by name). */
export interface PlannedSitting {
  id: string;
  skills: string[];
}

/**
 * Home: "Today: 20 problems, about 55 minutes". Never an overdue count (QUE-7). The old
 * engine's proposals and vacation went with it; the planner's notes replace the proposals.
 */
export interface TodayView {
  day: string;
  problems: number;
  minutes: number;
  flashcards: number;
  courses: CourseLine[];
  exams: ExamLine[];
  session_open: boolean;
  done_today: boolean;
  extra_practice_available: boolean;
  /** Leech flashcards, not shown until rewritten. */
  flashcards_to_rewrite?: number;
  /** Today's items by role (new, growth, maintenance, check, sitting ...). */
  by_role: Partial<Record<Role, number>>;
  /** Hours a week that keep every course on pace; null when there is no figure. */
  hours_to_keep_pace: number | null;
  hours_basis: HoursBasis;
  /** The courses' reference hours outside class per week. */
  standard_hours: number | null;
  /** Skills behind their milestone deadlines, by name. */
  behind: string[];
  /** Skills set aside for the rest of today (the stuck ladder's last rung), by name. */
  set_aside: string[];
  sittings: PlannedSitting[];
  /** The planner's notices, in plain words. */
  notes: string[];
}

/** A miss listed on the summary, with its tag. */
export interface MissLine {
  item_key: string;
  card_id: string | null;
  skill_id: string | null;
  skill_name: string;
  tag: string;
  label: string;
}

/** One practice-test problem's result. */
export interface TestLine {
  item_key: string;
  card_id: string | null;
  skill_name: string;
  answered: boolean;
  correct: boolean;
  your_answer: string | null;
  /** The review it counted as (null: not graded). */
  rating: number | null;
}

/** A practice test's result, given at the end like a real exam. */
export interface TestResult {
  exam_id: number | null;
  answered: number;
  correct: number;
  total: number;
  timed: boolean;
  time_up: boolean;
  lines: TestLine[];
  /** How unanswered problems counted: as misses (again) or not at all (skip). */
  unanswered: 'again' | 'skip';
  /** The time allowed when timed. */
  limit_ms: number | null;
}

/** The card shown when a session ends. */
export interface Summary {
  mode: string;
  problems: number;
  correct: number;
  missed: number;
  active_ms: number;
  misses: MissLine[];
  /** Skills learned in this session. */
  learned: string[];
  flashcards: number;
  forecast: Forecast;
  extra_practice_available: boolean;
  practice_tests: ExamLine[];
  test: TestResult | null;
  /** Learning-phase problems ready later today (a new skill's block goes on). */
  ready_today: number;
}

/** What the study screen shows next: an item (maybe already answered, after a resume), the summary, or nothing to do. */
export interface Turn {
  type: 'problem' | 'summary' | 'empty';
  session_id: number | null;
  problem: ProblemView | null;
  progress: Progress | null;
  /** The verdict screen, when resuming after an answer that was not continued from. */
  result: AttemptResult | null;
  summary: Summary | null;
  /**
   * A one-line note for the item on screen ("Undone. The problem is back.", or a skill set
   * aside for today with its textbook pointer). It stays until the next item.
   */
  message: string;
  break_due: boolean;
  /** The Lighter set went with the old engine; the page ignores this. */
  lighter: boolean;
  mode: string;
}

// ---------------------------------------------------------------------------
// Course setup (course_settings_get / _set, exam_save / _delete)
// ---------------------------------------------------------------------------

/** An exam as the student enters it (exam_save); `exam_id` is set when editing one. */
export interface ExamIn {
  exam_id?: number;
  course_id: string;
  name: string;
  /** The study day of the exam (YYYY-MM-DD). */
  day: string;
  /** The sections it covers, by deck. */
  scope_decks: string[];
  /** Its own accuracy target; null: the course's. */
  target?: number | null;
  /** How long it is. */
  minutes?: number | null;
  /** How many problems it has (a practice test uses the same number, else 10). */
  problems?: number | null;
}

/** A saved exam. */
export interface Exam extends ExamIn {
  exam_id: number;
}

/** A section of a course, in course order, with its class hours (null without pace data). */
export interface SectionRef {
  deck: string;
  title: string;
  hours: number | null;
}

/** A course's schedule and targets. */
export interface CourseSettings {
  course_id: string;
  course_title: string;
  /** The first class (YYYY-MM-DD), or null. */
  start: string | null;
  /** "My class is at section X today": the section and the day it was said. Wins over `start`. */
  aligned: { deck: string; day: string } | null;
  /** 0.75 to 1.5: how fast the class moves against the standard (higher is faster). */
  pace_factor: number;
  /** 0.80 to 0.95: the chance of a right first try to reach. */
  accuracy_target: number;
  /** 3 to 5: the tier that accuracy must hold at. */
  target_tier: number;
  /** The last day of the course (YYYY-MM-DD); after it, skills drop to Keep. Null: self-study. */
  end: string | null;
  keep_target: number;
  keep_tier: number;
  /** Practice difficulty: standard aims at 70-90% right, hard at 50-75%. */
  growth_band: 'standard' | 'hard';
  exams: Exam[];
  sections: SectionRef[];
  /** The pack gives class hours per section; without them nothing can be dated. */
  has_pace: boolean;
}

// ---------------------------------------------------------------------------
// Skills (skills_get)
// ---------------------------------------------------------------------------

/** One milestone of a skill: its tier, its deadline and whether it is certified. */
export interface MilestoneView {
  name: MilestoneName;
  tier: number;
  /** YYYY-MM-DD; null for Keep, or with no schedule. */
  deadline: string | null;
  certified: boolean;
}

/** One skill on the Skills screen. */
export interface SkillRow {
  skill_id: string;
  name: string;
  deck: string;
  /** not-introduced, new, growth, maintenance, keep, slip-limited, struggling. */
  state: string;
  track: 'ahead' | 'on-track' | 'behind';
  /** The day it is introduced (YYYY-MM-DD), or null with no schedule. */
  intro: string | null;
  milestones: MilestoneView[];
  /** The highest tier with every tier at or below it certified. */
  level: number | null;
  /** The calibrated predicted chance of a right first try at its current (or certified) tier. */
  readiness: number | null;
  /** Typical solve time at or under the standard time; null before any timed first try. */
  pace_ok: boolean | null;
  /** Set aside for the rest of today. */
  set_aside: boolean;
}

/** skills_get: one course's skills, in course order. */
export interface SkillsView {
  course_id: string;
  day: string;
  skills: SkillRow[];
}

// ---------------------------------------------------------------------------
// The student model (model_get, model_refit, model_reset)
// ---------------------------------------------------------------------------

/** One row of a calibration table: first tries, the mean predicted chance, the share right. */
export interface Bin {
  label: string;
  n: number;
  predicted: number;
  observed: number;
}

/** One block of parameters in a refit: held-out log loss per first try, before and after. */
export interface RefitBlock {
  /** accuracy or time. */
  name: string;
  current: number;
  candidate: number;
  p_value: number;
  adopted: boolean;
}

/** What a refit did. */
export interface RefitReport {
  /** When it ran (epoch ms). */
  at: number;
  /** First tries in the log it used. */
  attempts: number;
  /** Some block's new values were kept. */
  adopted: boolean;
  p_value: number;
  blocks: RefitBlock[];
}

/** The calibration tables: by tier, by days since the skill was practiced, by skills in the problem. */
export interface Calibration {
  by_tier: Bin[];
  by_gap: Bin[];
  by_components: Bin[];
}

/** The student model's current parameters and how well it has predicted. */
export interface ModelView {
  version: string;
  source: 'prior' | 'refit' | 'reset';
  /** When this version was made (epoch ms). */
  created_at: number;
  params: Record<string, number | number[]>;
  last_refit: RefitReport | null;
  calibration: Calibration;
  /** First tries in the log. */
  attempts: number;
}

// ---------------------------------------------------------------------------
// Profile, library, preferences
// ---------------------------------------------------------------------------

/** The open profile. */
export interface Profile {
  id: string;
  name: string;
}

/** profile_get: the open profile, or null on first run (the page asks for a name). */
export interface ProfileState {
  profile: Profile | null;
  /** Why no profile could be opened (in use elsewhere, damaged). */
  error: string | null;
  /** Startup warnings, such as a data folder inside a cloud-synced folder. */
  warnings: string[];
}

/** One verified backup, as the restore screen previews it (BAK-3). */
export interface BackupEntry {
  /** The backup's file name; pass it to restore_backup. */
  id: string;
  /** When it was taken (epoch ms). */
  created_at: number;
  /** periodic, close, manual, pre-migration, pre-import, pre-pack-update, pre-restore. */
  reason: string;
  attempts: number;
  last_attempt_at: number | null;
}

/**
 * restore_list: the profile to restore and its verified backups, newest first. While no
 * profile is open, `profile` is one that could not be opened (show the restore screen).
 */
export interface BackupList {
  profile: Profile | null;
  backups: BackupEntry[];
}

/** A section's state (spec: Library). 'mixed' only on a course or unit (LIB-1). */
export type SectionState = 'off' | 'learning' | 'covered' | 'solid';

/** A section of the course tree. */
export interface LibrarySection {
  id: string;
  title: string;
  state: SectionState;
  skills: number;
  textbook_ref: string | null;
  /** Skills with too few problems for the learning phase's run of correct answers (ENG-2):
   * each is learned after all its problems in a row ("pool too small"). */
  small_pool_skills: string[];
}

/** A unit of the course tree. */
export interface LibraryUnit {
  id: string;
  title: string;
  state: SectionState | 'mixed';
  sections: LibrarySection[];
}

/** A course of the course tree. */
export interface LibraryCourse {
  id: string;
  title: string;
  state: SectionState | 'mixed';
  units: LibraryUnit[];
}

/** library_get: the course tree. */
export interface Library {
  courses: LibraryCourse[];
}

/** library_set_state: a course or unit sets all its sections. */
export interface LibraryStateRequest {
  id: string;
  state: SectionState;
}

/** library_card_media: the media of one card. */
export interface CardMediaRequest {
  card_id: string;
}

/**
 * The media a card's text refers to (ADR-0017): each reference as the card writes it
 * (`pic.png`, `media/graph.svg`, `_anki-nt-....css`) to a URL on this page's own origin
 * (`/media/user/<sha256>.png`, `/media/pack/<pack>/<name>`). References without a stored
 * file are absent.
 */
export interface CardMedia {
  files: Record<string, string>;
}

/** Automatic follows the operating system's light or dark setting. */
export type ThemeChoice = 'auto' | 'day' | 'night';

/** Appearance preferences (prefs_get / prefs_set), kept in the profile. */
export interface Preferences {
  theme: ThemeChoice;
  /** Problem text size in px, 14 to 28; the interface and math scale with it. */
  text_size: number;
}

export const TEXT_SIZE_MIN = 14;
export const TEXT_SIZE_MAX = 28;
export const TEXT_SIZE_DEFAULT = 18;
