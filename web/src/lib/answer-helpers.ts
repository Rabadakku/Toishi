import type { AnswerType } from './types';

/**
 * Answer-shape helpers (MATH-7): for intervals, sets and points the answer box offers
 * brackets, union, infinity, DNE and none as buttons. Each button inserts LaTeX in the math
 * field and the card format's plain-text spelling in plain-text mode.
 */
export interface ShapeHelper {
  id: string;
  /** What the button shows. */
  label: string;
  /** Spoken name. */
  name: string;
  latex: string;
  text: string;
}

const OPEN_PAREN: ShapeHelper = { id: 'open-paren', label: '(', name: 'Open parenthesis', latex: '(', text: '(' };
const CLOSE_PAREN: ShapeHelper = { id: 'close-paren', label: ')', name: 'Close parenthesis', latex: ')', text: ')' };
const OPEN_BRACKET: ShapeHelper = { id: 'open-bracket', label: '[', name: 'Open square bracket', latex: '[', text: '[' };
const CLOSE_BRACKET: ShapeHelper = { id: 'close-bracket', label: ']', name: 'Close square bracket', latex: ']', text: ']' };
const UNION: ShapeHelper = { id: 'union', label: '∪', name: 'Union', latex: '\\cup ', text: ' U ' };
const INFINITY: ShapeHelper = { id: 'infinity', label: '∞', name: 'Infinity', latex: '\\infty ', text: 'inf' };
const DNE: ShapeHelper = { id: 'dne', label: 'DNE', name: 'Does not exist', latex: '\\mathrm{DNE}', text: 'DNE' };
const NONE: ShapeHelper = { id: 'none', label: 'none', name: 'None, the empty set', latex: '\\mathrm{none}', text: 'none' };

export function helpersFor(type: AnswerType): ShapeHelper[] {
  switch (type) {
    case 'interval':
      return [OPEN_PAREN, CLOSE_PAREN, OPEN_BRACKET, CLOSE_BRACKET, UNION, INFINITY, DNE, NONE];
    case 'set':
    case 'list':
      return [INFINITY, DNE, NONE];
    case 'point':
      return [OPEN_PAREN, CLOSE_PAREN, INFINITY];
    default:
      return [];
  }
}
