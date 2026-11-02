import '@fontsource-variable/inter/wght.css';
import '@fontsource-variable/source-serif-4/wght.css';
import '@fontsource-variable/source-serif-4/wght-italic.css';
import 'katex/dist/katex.min.css';
import 'mathlive/fonts.css';
import './styles/tokens.css';
import './styles/base.css';

import { MathfieldElement } from 'mathlive';
import { mount } from 'svelte';
import App from './App.svelte';
import { installDropGuard } from './lib/drop-guard';
import { installMockBridge, mockBridgeRequested } from './lib/mock-bridge';

// Everything MathLive needs is bundled: fonts via mathlive/fonts.css (so no
// dynamic font loading), sounds emitted to ./mathlive/sounds by vite.config.ts.
MathfieldElement.fontsDirectory = null;
MathfieldElement.soundsDirectory = new URL('mathlive/sounds/', document.baseURI).href;
// No sounds by default (spec: Design and theme > Long sessions).
MathfieldElement.keypressSound = null;
MathfieldElement.plonkSound = null;
// Answer checking happens in Python (SymPy); MathLive's compute engine is not used.
MathfieldElement.computeEngine = null;

installDropGuard();
if (mockBridgeRequested()) installMockBridge();

const target = document.getElementById('app');
if (!target) throw new Error('#app element missing');

export default mount(App, { target });
