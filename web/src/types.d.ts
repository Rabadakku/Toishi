import type { MathfieldElement } from 'mathlive';
import type { HTMLAttributes } from 'svelte/elements';

declare module 'svelte/elements' {
  export interface SvelteHTMLElements {
    'math-field': HTMLAttributes<MathfieldElement> & {
      'math-virtual-keyboard-policy'?: 'auto' | 'manual' | 'sandboxed';
    };
  }
}

export {};
