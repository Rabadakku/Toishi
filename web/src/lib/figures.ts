/** Figures bundled with the app, by the relative path a problem's Markdown uses. */
const urls = import.meta.glob<string>('../assets/figures/*.svg', {
  eager: true,
  query: '?url',
  import: 'default',
});

export function resolveFigure(src: string): string | null {
  const match = /^figures\/([\w-]+\.svg)$/.exec(src);
  if (!match) return null;
  return urls[`../assets/figures/${match[1]}`] ?? null;
}
