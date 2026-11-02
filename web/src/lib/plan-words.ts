/**
 * The planner's codes in plain words (roles, reasons, skill states, tracks, milestones,
 * tiers), shared by Home, the study screen and the Skills screen. Words, not jargon: the
 * student sees "Building", never "growth role".
 */
import type { HoursBasis, MilestoneName, Role, SkillRow, Textbook, TodayView } from './types';

/** Each role as Home lists it: a word and what it means. */
export const ROLE_WORDS: Record<Role, { label: string; hint: string }> = {
  new: { label: 'New', hint: 'The first problems on a skill your class has reached' },
  growth: { label: 'Building', hint: 'Problems at the tier a skill is working toward' },
  maintenance: { label: 'Review', hint: 'A skill you have reached, kept from fading' },
  check: { label: 'Check', hint: 'A spot check that a skill has held' },
  sitting: { label: 'Sitting', hint: 'A closed-book, timed set that certifies a level' },
  'practice-test': { label: 'Practice test', hint: 'A timed test before an exam' },
  focused: { label: 'Focused', hint: 'Practice on one section or skill' },
};

/** The order Home lists roles in. */
export const ROLE_ORDER: readonly Role[] = ['new', 'growth', 'maintenance', 'check', 'sitting', 'practice-test', 'focused'];

/** The stuck ladder's short line on the item it changed (from `plan_reason`), or null for any other item. */
export function ladderWords(code: string | null | undefined): string | null {
  if (code === 'ladder:smaller') return 'A smaller step first';
  if (code === 'ladder:prerequisite') return 'A prerequisite first';
  return null;
}

/** "OpenStax Calculus Volume 1 §4.1". */
export function textbookLine(textbook: Textbook): string {
  const section = textbook.section.trim().replace(/^§\s*/, '');
  return section ? `${textbook.book} §${section}` : textbook.book;
}

/** A skill's state, as the Skills screen says it. */
export const STATE_WORDS: Record<string, { label: string; hint: string }> = {
  'not-introduced': { label: 'Not started', hint: 'Your class has not reached it yet' },
  new: { label: 'New today', hint: 'Its first problems start today' },
  growth: { label: 'Building', hint: 'Working toward its next level' },
  maintenance: { label: 'Reviewing', hint: 'Its level is reached; reviews keep it there' },
  keep: { label: 'Keeping', hint: 'The course is over; light reviews keep it fresh' },
  'slip-limited': { label: 'Careless errors', hint: 'You know it, but slips hold it back. Check your work.' },
  struggling: { label: 'Struggling', hint: 'Many tries without progress. Go back to the textbook section.' },
};

export function stateWords(state: string): { label: string; hint: string } {
  return STATE_WORDS[state] ?? { label: state, hint: '' };
}

/** Ahead, on track or behind its milestone deadlines. */
export const TRACK_WORDS: Record<SkillRow['track'], string> = {
  ahead: 'Ahead',
  'on-track': 'On track',
  behind: 'Behind',
};

/** The milestones in plain words; the tier goes alongside. */
export const MILESTONE_WORDS: Record<MilestoneName, string> = {
  M1: 'Homework level',
  M2: 'Exam level',
  M3: 'Target level',
  keep: 'Keep',
};

/** The difficulty tiers (card format: Difficulty tiers). */
export const TIER_WORDS: Record<number, { label: string; hint: string }> = {
  1: { label: 'Drill', hint: 'One step, one skill' },
  2: { label: 'Standard', hint: 'Routine homework on one section' },
  3: { label: 'Exam', hint: 'A standard exam problem at a good university' },
  4: { label: 'Challenge', hint: 'Above the standard exam: skills combined, no hint of the method' },
  5: { label: 'Elite', hint: 'Advanced, in optional sections' },
};

/** "A", "A and B", "A, B and C". */
export function listText(names: readonly string[]): string {
  if (names.length <= 1) return names[0] ?? '';
  return `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`;
}

function hours(value: number): string {
  const rounded = Math.round(value * 2) / 2; // to the half hour
  return `${rounded} hour${rounded === 1 ? '' : 's'}`;
}

/** Home's pace line and where its figure comes from (wave 2 section 5: say which). */
export function paceWords(today: Pick<TodayView, 'hours_to_keep_pace' | 'hours_basis' | 'standard_hours'>): {
  line: string;
  basis: string;
} {
  const basis: HoursBasis = today.hours_basis;
  if (basis === 'none' || today.hours_to_keep_pace === null) {
    return { line: 'No pace figure yet.', basis: 'Your courses have no pace data to work it out from.' };
  }
  const line = `About ${hours(today.hours_to_keep_pace)} a week keeps you on pace.`;
  if (basis === 'history') {
    const standard = today.standard_hours === null ? '' : ` The course standard is ${hours(today.standard_hours)}.`;
    return { line, basis: `Worked out from your own practice so far.${standard}` };
  }
  return {
    line,
    basis: "This is the course standard. It switches to a figure from your own practice once you've certified about 10 milestones.",
  };
}
