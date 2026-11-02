import { readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig, type Plugin } from 'vite';

const outDir = fileURLToPath(new URL('../app/web_dist', import.meta.url));

/**
 * Emit MathLive's sound files next to the page (mathlive/sounds/*.wav) so the
 * virtual keyboard never reaches for a remote copy. Fonts come from
 * `mathlive/fonts.css`, which Vite rewrites and emits like any other asset.
 */
function mathliveSounds(): Plugin {
  const dir = fileURLToPath(new URL('./node_modules/mathlive/sounds/', import.meta.url));
  return {
    name: 'toishi:mathlive-sounds',
    apply: 'build',
    generateBundle() {
      for (const name of readdirSync(dir)) {
        this.emitFile({
          type: 'asset',
          fileName: `mathlive/sounds/${name}`,
          source: readFileSync(dir + name),
        });
      }
    },
  };
}

export default defineConfig({
  // Relative URLs: the page is served from pywebview's loopback server on a random port.
  base: './',
  plugins: [svelte(), mathliveSounds()],
  build: {
    outDir,
    emptyOutDir: true,
    // Never inline fonts/images as data: URIs, so the CSP can stay at font-src 'self'.
    assetsInlineLimit: 0,
    sourcemap: false,
    reportCompressedSize: false,
    // One local bundle is fine: it is read from disk over loopback, never downloaded.
    chunkSizeWarningLimit: 2048,
    // Third-party licenses of everything bundled (Svelte, KaTeX, MathLive).
    license: { fileName: 'licenses/THIRD-PARTY-LICENSES.md' },
  },
  server: { host: '127.0.0.1', strictPort: true },
});
