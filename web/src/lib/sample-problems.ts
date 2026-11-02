import type { AnswerType, CardView, ItemKind, PartView, Reason, Role, SittingView, StepView, Textbook } from './types';

/**
 * Sample items for the mock bridge only (page tests, `npm run dev`). Each carries the
 * CardView the page sees plus what Python would hold (keys, the worked solution, what the
 * planner said about it). Nothing here reaches the page in the app: there the core serves
 * the real packs.
 */

export interface WrongAnswer {
  /** Plain-text spelling of the wrong answer (compared after normalising). */
  answer: string;
  feedback: string;
}

export interface PartKey {
  /** Accepted answers in plain-text spelling; for choice parts the 1-based numbers ("4"). */
  accept: string[];
  /** Numeric parts compare within this relative tolerance instead of as text. */
  tolerance?: number;
  wrong?: WrongAnswer[];
}

export interface SampleItem {
  kind: ItemKind;
  card: CardView;
  reason: Reason;
  skill: { id: string; name: string };
  /** By part label ('main' for a single box). */
  keys: Record<string, PartKey>;
  steps: StepView[];
  answer_md: string | null;
  alternative_md?: string;
  target_ms: number | null;
  /** Find-the-error: the index of the right reason. */
  right_reason?: number;
  /** What the planner said about it (the problem view's role and reason code). */
  role: Role | null;
  plan_reason: string | null;
  textbook: Textbook | null;
  /** A closed-book sitting item; the mock fills in the block's elapsed time when serving it. */
  sitting?: Omit<SittingView, 'block_elapsed_ms'> | null;
  /** The planned slot of a skill that the stuck ladder may rewrite (the ladder session). */
  slot?: string;
}

/** The stuck ladder for one skill (the ladder session): what replaces its next slots. */
export interface LadderPlan {
  skill: { id: string; name: string };
  /** Rung 1, after one first-try miss in a row: a problem one tier lower. */
  smaller: SampleItem;
  /** Rung 2, after two: a problem on a prerequisite. */
  prerequisite: SampleItem;
  /** Rung 3, after three: the skill is set aside today, with this pointer. */
  textbook: Textbook;
}

/** A sample session: its items in order, and the ladder when it has one. */
export interface SampleSession {
  items: SampleItem[];
  ladder: LadderPlan | null;
}

function step(number: number, skill_id: string | null, skill_name: string | null, label: string, body_md: string): StepView {
  return { number, skill_id, skill_name, label, body_md };
}

function part(answer_type: AnswerType, label: string | null = null, prompt_md: string | null = null, choices: string[] = []): PartView {
  return { label, prompt_md, answer_type, choices: choices.map((text_md, index) => ({ index, text_md })) };
}

function card(id: string, kind: CardView['kind'], prompt_md: string, parts: PartView[], extra: Partial<CardView> = {}): CardView {
  return {
    id,
    rev: 1,
    kind,
    prompt_md,
    parts,
    calculator: false,
    angles: 'radians',
    plot: null,
    self_graded: false,
    back_md: null,
    solution_md: null,
    shown_work: [],
    reasons: [],
    error_step: null,
    cloze: null,
    type_answer: false,
    ...extra,
  };
}

const CALCULUS = 'OpenStax Calculus Volume 1';
const ALGEBRA = 'OpenStax College Algebra 2e';
const TRIGONOMETRY = 'OpenStax Algebra and Trigonometry 2e';

function book(title: string, section: string): Textbook {
  return { book: title, section };
}

const powerRule = { id: 'calc1.deriv.power-rule', name: 'Power rule' };
const factoring = { id: 'alg.factor.polynomials', name: 'Factoring polynomials' };

const derivative: SampleItem = {
  kind: 'problem',
  skill: powerRule,
  card: card('calc1.2-3.power-quartic.001', 'problem', "Find \\(f'(x)\\) for \\(f(x) = x^4 - 2x^2\\).", [part('expression')]),
  reason: {
    tag: 'review',
    label: 'Review',
    why: 'You last practiced this skill nine days ago. A short review now keeps your recall near 90%, so it does not slip.',
  },
  keys: {
    main: {
      accept: ['4x^3-4x', '4x(x^2-1)', '4x(x-1)(x+1)', '4(x^3-x)'],
      wrong: [
        {
          answer: '4x^3-2x',
          feedback: 'The second term differentiates to \\(4x\\): multiply by the exponent, then lower it by one.',
        },
        { answer: '4x^3', feedback: 'The second term is missing: it also needs differentiating.' },
      ],
    },
  },
  steps: [
    step(0, powerRule.id, powerRule.name, 'Set up', 'The function is a sum, so differentiate each term with the power rule.'),
    step(1, powerRule.id, powerRule.name, 'Differentiate', "\\(f'(x) = 4x^3 - 2\\cdot 2x = 4x^3 - 4x\\)."),
    step(2, factoring.id, factoring.name, 'Factor (optional)', "\\(f'(x) = 4x(x - 1)(x + 1)\\)."),
  ],
  answer_md: '\\(4x^3 - 4x\\)',
  alternative_md: "Factor first: \\(f(x) = x^2(x^2 - 2)\\), then use the product rule. The result is the same, \\(4x^3 - 4x\\).",
  target_ms: 150_000,
  role: 'maintenance',
  plan_reason: 'target',
  textbook: book(CALCULUS, '3.3'),
};

const powerExample: SampleItem = {
  kind: 'example',
  skill: powerRule,
  card: card('calc1.2-3.power-example.001', 'example', "Worked example: find \\(g'(x)\\) for \\(g(x) = 3x^5\\).", [part('self')], {
    solution_md: "Multiply by the exponent and lower it by one: \\(g'(x) = 15x^4\\).",
  }),
  reason: { tag: 'new-skill', label: 'New skill', why: 'A worked example comes first when a skill is new.' },
  keys: {},
  steps: [],
  answer_md: null,
  target_ms: null,
  role: 'new',
  plan_reason: 'example',
  textbook: book(CALCULUS, '3.3'),
};

const derivativeFlashcard: SampleItem = {
  kind: 'flashcard',
  skill: powerRule,
  card: card('calc1.flash.power-rule', 'flashcard', 'The power rule: \\(\\dfrac{d}{dx}\\,x^n = \\;?\\)', [part('self')], {
    self_graded: true,
    back_md: '\\(n\\,x^{n-1}\\)',
  }),
  reason: { tag: 'review', label: 'Flashcard', why: 'A flashcard due today.' },
  keys: {},
  steps: [],
  answer_md: null,
  target_ms: null,
  role: null,
  plan_reason: null,
  textbook: null,
};

const firstDerivativeTest = { id: 'calc1.shape.first-derivative-test', name: 'First derivative test' };

const cubicShape: SampleItem = {
  kind: 'problem',
  skill: firstDerivativeTest,
  card: card('calc1.4-3.cubic-shape.001', 'problem', 'Let \\(f(x) = x^3 - 3x^2\\).', [
    part('interval', 'a', 'On what intervals is \\(f\\) increasing?'),
    part('point', 'b', 'Find the local maximum point.'),
    part('point', 'c', 'Find the local minimum point.'),
  ]),
  reason: {
    tag: 'new-skill',
    label: 'New skill',
    why: 'This skill was introduced recently. Practice now, spaced a little apart, is how it becomes lasting.',
  },
  keys: {
    a: {
      accept: ['(-inf,0)u(2,inf)'],
      wrong: [{ answer: '(0,2)', feedback: "That is where \\(f\\) is decreasing: \\(f'\\) is negative on \\((0, 2)\\)." }],
    },
    b: { accept: ['(0,0)'], wrong: [{ answer: '(2,-4)', feedback: 'That is the minimum.' }] },
    c: { accept: ['(2,-4)'] },
  },
  steps: [
    step(0, firstDerivativeTest.id, firstDerivativeTest.name, 'Set up', "\\(f\\) increases where \\(f' > 0\\), and has extremes where \\(f'\\) changes sign."),
    step(1, powerRule.id, powerRule.name, 'Differentiate', "\\(f'(x) = 3x^2 - 6x\\)."),
    step(2, factoring.id, factoring.name, 'Factor', "\\(f'(x) = 3x(x - 2)\\)."),
    step(3, firstDerivativeTest.id, firstDerivativeTest.name, 'Sign chart', "\\(f' > 0\\) for \\(x < 0\\) and \\(x > 2\\)."),
    step(4, firstDerivativeTest.id, firstDerivativeTest.name, 'Classify', 'A local maximum at \\((0, 0)\\) and a local minimum at \\((2, -4)\\).'),
  ],
  answer_md: '(a) \\((-\\infty, 0) \\cup (2, \\infty)\\) (b) \\((0, 0)\\) (c) \\((2, -4)\\)',
  target_ms: 240_000,
  role: 'new',
  plan_reason: 'new',
  textbook: book(CALCULUS, '4.5'),
};

const chainRule = { id: 'calc1.deriv.chain-rule', name: 'Chain rule' };

const chainError: SampleItem = {
  kind: 'problem',
  skill: chainRule,
  card: card(
    'calc1.3-4.chain-error.001',
    'find-error',
    "Another student found \\(f'(x)\\) for \\(f(x) = (x^2 + 1)^3\\). One step is wrong.",
    [part('expression')],
    {
      shown_work: [
        step(1, null, null, 'Outer function', '\\(u^3\\) with \\(u = x^2 + 1\\).'),
        step(2, null, null, 'Differentiate', "\\(f'(x) = 3(x^2 + 1)^2\\)."),
        step(3, null, null, 'Done', "\\(f'(x) = 3(x^2 + 1)^2\\)."),
      ],
      reasons: [
        'The power rule was applied to the wrong exponent',
        'The derivative of the inner function, \\(2x\\), is missing',
        'The inner function should be cubed before differentiating',
      ].map((text_md, index) => ({ index, text_md })),
    },
  ),
  right_reason: 1,
  reason: { tag: 'check', label: 'Check', why: 'Spotting a mistake in worked work is a different skill from avoiding it.' },
  keys: { main: { accept: ['6x(x^2+1)^2'] } },
  steps: [
    step(1, chainRule.id, chainRule.name, 'Outer function', '\\(u^3\\) with \\(u = x^2 + 1\\).'),
    step(2, chainRule.id, chainRule.name, 'Chain rule', "\\(f'(x) = 3(x^2 + 1)^2 \\cdot 2x\\)."),
  ],
  answer_md: '\\(6x(x^2 + 1)^2\\)',
  target_ms: 120_000,
  role: 'check',
  plan_reason: 'check',
  textbook: book(CALCULUS, '3.6'),
};

const limitTechnique = { id: 'calc1.select.limit-technique', name: 'Choosing a limit technique' };

const whichMethod: SampleItem = {
  kind: 'problem',
  skill: limitTechnique,
  card: card(
    'calc1.4-4.method-limit.001',
    'method',
    'Which method fits? Do not solve it.\n\n\\[\\lim_{x \\to 0} \\frac{\\sin 3x}{x}\\]',
    [
      part('choice', null, null, [
        'Direct substitution',
        'Factor and cancel',
        'Multiply by the conjugate',
        "L'Hôpital's rule, or the known limit of \\(\\sin u / u\\)",
      ]),
    ],
  ),
  reason: { tag: 'review', label: 'Review', why: 'Choosing the method is the hard part of many problems.' },
  keys: { main: { accept: ['4'] } },
  steps: [step(0, limitTechnique.id, limitTechnique.name, 'Set up', "Substitution gives \\(0/0\\) and the top is a sine, so use L'Hôpital's rule.")],
  answer_md: "L'Hôpital's rule",
  target_ms: 15_000,
  role: 'maintenance',
  plan_reason: 'target',
  textbook: book(CALCULUS, '4.8'),
};

const averageRate = { id: 'calc1.rates.average-rate', name: 'Average rate of change' };

const tableRate: SampleItem = {
  kind: 'problem',
  skill: averageRate,
  card: card(
    'calc1.2-1.avg-rate-table.001',
    'problem',
    'The table gives values of a function \\(f\\).\n\n| \\(x\\) | 1 | 2 | 3 |\n| :-- | --: | --: | --: |\n| \\(f(x)\\) | 4.2 | 5.9 | 9.0 |\n\nFind the average rate of change of \\(f\\) from \\(x = 1\\) to \\(x = 3\\).',
    [part('number')],
    { calculator: true },
  ),
  reason: {
    tag: 'review',
    label: 'Building',
    why: 'This skill is working toward its next level, so it gets a few problems a day at that tier.',
  },
  keys: {
    main: {
      accept: ['2.4'],
      tolerance: 0.001,
      wrong: [{ answer: '4.8', feedback: 'That is the change in \\(f\\). Divide by the change in \\(x\\) too.' }],
    },
  },
  steps: [
    step(0, averageRate.id, averageRate.name, 'Set up', 'Average rate of change is \\(\\dfrac{f(3) - f(1)}{3 - 1}\\).'),
    step(1, 'alg.read-tables', 'Reading tables', 'Read the table', '\\(f(3) = 9.0\\) and \\(f(1) = 4.2\\).'),
    step(2, averageRate.id, averageRate.name, 'Compute', '\\(\\dfrac{9.0 - 4.2}{2} = 2.4\\).'),
  ],
  answer_md: '\\(2.4\\)',
  target_ms: 120_000,
  role: 'growth',
  plan_reason: 'band',
  textbook: book(CALCULUS, '3.1'),
};

const rightTriangles = { id: 'trig.right-triangle.sine', name: 'Right-triangle trigonometry' };

const ladder: SampleItem = {
  kind: 'problem',
  skill: rightTriangles,
  card: card(
    'trig.right-triangle.ladder.001',
    'problem',
    'A 6 m ladder leans against a wall and makes an angle of \\(40^\\circ\\) with the ground.\n\n![A ladder leaning against a wall, 6 m long, at 40 degrees to the ground](figures/ladder.svg)\n\nHow far up the wall does it reach? Round to 2 decimal places.',
    [part('number')],
    { calculator: true, angles: 'degrees' },
  ),
  reason: { tag: 'review', label: 'Review', why: 'A routine review of a skill you know well, so it stays that way.' },
  keys: {
    main: {
      accept: ['3.86'],
      tolerance: 0.002,
      wrong: [{ answer: '4.60', feedback: 'That uses cosine; the height is opposite the angle.' }],
    },
  },
  steps: [
    step(0, rightTriangles.id, rightTriangles.name, 'Set up', 'The ladder is the hypotenuse, so \\(\\sin 40^\\circ = h/6\\).'),
    step(1, rightTriangles.id, rightTriangles.name, 'Solve for h', '\\(h = 6 \\sin 40^\\circ\\).'),
    step(2, 'trig.calculator-degrees', 'Calculator in degree mode', 'Calculate', '\\(h \\approx 3.86\\) m.'),
  ],
  answer_md: '\\(3.86\\)',
  target_ms: 180_000,
  role: 'maintenance',
  plan_reason: 'target',
  textbook: book(TRIGONOMETRY, '7.2'),
};

function copy(item: SampleItem): SampleItem {
  return { ...item, card: { ...item.card } };
}

/** The daily mock session, in order: six problems, a worked example and a flashcard between them. */
export function sampleItems(): SampleItem[] {
  return [derivative, cubicShape, powerExample, chainError, whichMethod, derivativeFlashcard, tableRate, ladder].map(copy);
}

// --- the stuck ladder (?scenario=ladder) -------------------------------------

/** A one-step derivative of a sum of powers: the power rule's planned growth problems. */
function powerProblem(id: string, f: string, answer: string, answerMd: string, wrong: WrongAnswer[] = []): SampleItem {
  return {
    kind: 'problem',
    skill: powerRule,
    card: card(id, 'problem', `Find \\(f'(x)\\) for \\(f(x) = ${f}\\).`, [part('expression')]),
    reason: {
      tag: 'review',
      label: 'Building',
      why: 'This skill is working toward its next level, so it gets a few problems a day at that tier.',
    },
    keys: { main: { accept: [answer], wrong } },
    steps: [
      step(0, powerRule.id, powerRule.name, 'Set up', 'A sum of powers: differentiate each term with the power rule.'),
      step(1, powerRule.id, powerRule.name, 'Differentiate', `\\(f'(x) = ${answerMd}\\).`),
    ],
    answer_md: `\\(${answerMd}\\)`,
    target_ms: 150_000,
    role: 'growth',
    plan_reason: 'band',
    textbook: book(CALCULUS, '3.3'),
    slot: powerRule.id,
  };
}

const exponentRules = { id: 'alg.exponents.product', name: 'Exponent rules' };

/** Three planned power-rule problems, then a chain-rule problem. */
export function ladderSession(): SampleSession {
  const smaller: SampleItem = {
    ...powerProblem('calc1.2-3.power-single.001', 'x^5', '5x^4', '5x^4'),
    reason: {
      tag: 'relearn',
      label: 'Smaller step',
      why: 'The last problem on this skill was missed on the first try, so this one is a step smaller.',
    },
    plan_reason: 'ladder:smaller',
  };
  const prerequisite: SampleItem = {
    kind: 'problem',
    skill: exponentRules,
    card: card('alg.exponents.product.001', 'problem', 'Simplify \\(x^3 \\cdot x^4\\).', [part('expression')]),
    reason: {
      tag: 'relearn',
      label: 'Prerequisite',
      why: 'Two first tries in a row on a skill were missed, so this problem practices a skill it builds on.',
    },
    keys: { main: { accept: ['x^7'], wrong: [{ answer: 'x^12', feedback: 'Multiplying powers adds the exponents.' }] } },
    steps: [step(0, exponentRules.id, exponentRules.name, 'Add the exponents', '\\(x^3 \\cdot x^4 = x^{3+4} = x^7\\).')],
    answer_md: '\\(x^7\\)',
    target_ms: 60_000,
    role: 'growth',
    plan_reason: 'ladder:prerequisite',
    textbook: book(ALGEBRA, '1.2'),
  };
  const after: SampleItem = {
    kind: 'problem',
    skill: chainRule,
    card: card('calc1.3-6.chain-linear.001', 'problem', "Find \\(f'(x)\\) for \\(f(x) = (2x + 1)^3\\).", [part('expression')]),
    reason: { tag: 'review', label: 'Review', why: 'A short review keeps this skill from slipping.' },
    keys: { main: { accept: ['6(2x+1)^2'] } },
    steps: [step(0, chainRule.id, chainRule.name, 'Chain rule', "\\(f'(x) = 3(2x + 1)^2 \\cdot 2 = 6(2x + 1)^2\\).")],
    answer_md: '\\(6(2x + 1)^2\\)',
    target_ms: 150_000,
    role: 'maintenance',
    plan_reason: 'target',
    textbook: book(CALCULUS, '3.6'),
  };
  return {
    items: [
      powerProblem('calc1.2-3.power-sum.001', '3x^5 - 4x^3 + 7x', '15x^4-12x^2+7', '15x^4 - 12x^2 + 7', [
        { answer: '15x^4-12x^2', feedback: 'The last term, \\(7x\\), differentiates to \\(7\\).' },
      ]),
      powerProblem('calc1.2-3.power-sum.002', 'x^6 - 2x^4 + x', '6x^5-8x^3+1', '6x^5 - 8x^3 + 1'),
      powerProblem('calc1.2-3.power-sum.003', '2x^7 + 5x^2', '14x^6+10x', '14x^6 + 10x'),
      after,
    ].map(copy),
    ladder: { skill: powerRule, smaller, prerequisite, textbook: book(CALCULUS, '3.3') },
  };
}

// --- a closed-book sitting (?scenario=sitting) -------------------------------

const SITTING_ID = 'sitting-sample';

function sittingProblem(
  id: string,
  skill: { id: string; name: string },
  f: string,
  answer: string,
  answerMd: string,
  index: number,
  blockMs: number,
  section: string,
): SampleItem {
  return {
    kind: 'problem',
    skill,
    card: card(id, 'problem', `Find \\(f'(x)\\) for \\(f(x) = ${f}\\).`, [part('expression')]),
    reason: {
      tag: 'check',
      label: 'Sitting',
      why: 'A closed-book, timed set of new problems. Passing it certifies this skill at tier 3.',
    },
    keys: { main: { accept: [answer] } },
    steps: [step(0, skill.id, skill.name, 'Differentiate', `\\(f'(x) = ${answerMd}\\).`)],
    answer_md: `\\(${answerMd}\\)`,
    target_ms: blockMs / 2,
    role: 'sitting',
    plan_reason: 'sitting',
    textbook: book(CALCULUS, section), // the page hides it: a sitting is closed-book
    sitting: { id: SITTING_ID, index, total: 4, time_limit_ms: blockMs },
  };
}

/** A warm-up problem, then a sitting of two skill blocks of two problems each. */
export function sittingSession(): SampleSession {
  const powerBlock = 8 * 60_000; // two problems of 4 minutes' standard time
  const chainBlock = 10 * 60_000; // two of 5 minutes
  const warmUp: SampleItem = {
    ...powerProblem('calc1.2-3.power-warm.001', 'x^3 + 2x', '3x^2+2', '3x^2 + 2'),
    slot: undefined,
  };
  return {
    items: [
      warmUp,
      sittingProblem('calc1.2-3.power-sit.001', powerRule, '4x^5 - x^2 + 9', '20x^4-2x', '20x^4 - 2x', 1, powerBlock, '3.3'),
      sittingProblem('calc1.2-3.power-sit.002', powerRule, '6x^4 + 3x', '24x^3+3', '24x^3 + 3', 2, powerBlock, '3.3'),
      sittingProblem('calc1.3-6.chain-sit.001', chainRule, '(x^2 - 3)^4', '8x(x^2-3)^3', '8x(x^2 - 3)^3', 3, chainBlock, '3.6'),
      sittingProblem('calc1.3-6.chain-sit.002', chainRule, '(3x + 2)^5', '15(3x+2)^4', '15(3x + 2)^4', 4, chainBlock, '3.6'),
    ].map(copy),
    ladder: null,
  };
}
