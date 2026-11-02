import katex from 'katex';
import type { MathfieldElement } from 'mathlive';
import type { BridgeApi, SelfTestCheck, SelfTestReport } from './bridge';

const PROBE_LATEX = String.raw`\frac{1}{2}`;
const PROBE_FORMULA = String.raw`x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}`;

function nextTask(): Promise<void> {
  // Not requestAnimationFrame: a hidden window (the --self-test run) may never fire it.
  return new Promise((resolve) => window.setTimeout(resolve, 0));
}

/**
 * Checks that the page really works where it runs: CSP present, KaTeX rendered
 * with its fonts, MathLive mounted and editable, Python bridge round trip.
 * Used by `app --self-test`, the Qt spike and the Playwright tests. It builds its own
 * probe elements off screen, so it does not depend on which screen is showing.
 */
export async function runSelfTest(api: BridgeApi): Promise<SelfTestReport> {
  const checks: SelfTestCheck[] = [];
  const check = async (name: string, run: () => string | Promise<string>): Promise<void> => {
    try {
      checks.push({ name, ok: true, detail: await run() });
    } catch (error) {
      checks.push({ name, ok: false, detail: error instanceof Error ? error.message : String(error) });
    }
  };

  const probe = document.createElement('div');
  probe.className = 'selftest-probe';
  probe.setAttribute('aria-hidden', 'true');
  document.body.appendChild(probe);

  try {
    await check('csp', () => {
      const meta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
      const policy = meta?.getAttribute('content') ?? '';
      if (!policy.includes("default-src 'self'")) throw new Error('CSP meta tag missing');
      if (policy.includes('unsafe-eval')) throw new Error("CSP allows 'unsafe-eval'");
      return 'present';
    });

    await check('katex', () => {
      const formula = document.createElement('div');
      probe.appendChild(formula);
      katex.render(PROBE_FORMULA, formula, { displayMode: true, throwOnError: true, output: 'htmlAndMathml' });
      if (!formula.querySelector('.katex .katex-html')) throw new Error('no KaTeX HTML output');
      if (!formula.querySelector('.katex-mathml math')) throw new Error('no KaTeX MathML output');
      if (formula.querySelector('.katex-error')) throw new Error('KaTeX reported an error');
      return 'rendered';
    });

    await check('katex-fonts', async () => {
      const faces = await document.fonts.load('16px KaTeX_Main', 'x');
      if (faces.length === 0) throw new Error('KaTeX_Main font did not load');
      return `${faces.length} face(s) loaded`;
    });

    await check('mathlive', async () => {
      if (!customElements.get('math-field')) throw new Error('<math-field> is not defined');
      const field = document.createElement('math-field') as MathfieldElement;
      probe.appendChild(field);
      await nextTask();
      if (!field.shadowRoot) throw new Error('<math-field> did not mount');
      field.setValue(PROBE_LATEX, { silenceNotifications: true });
      const after = field.getValue();
      if (after !== PROBE_LATEX) throw new Error(`value round trip gave ${after}`);
      return 'mounted, value round trip ok';
    });

    await check('bridge', async () => {
      const reply = await api.ping('self-test');
      if (reply !== 'pong: self-test') throw new Error(`unexpected reply ${JSON.stringify(reply)}`);
      return reply;
    });
  } finally {
    probe.remove();
  }

  return { ok: checks.every((c) => c.ok), checks, page_ms: Math.round(performance.now()) };
}
