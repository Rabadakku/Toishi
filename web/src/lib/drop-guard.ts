/**
 * ARC-12 (HAZ-4): a file or link dropped on the window must never navigate it, because
 * pywebview hands the bridge to whatever page the window loads. Drags that carry files or
 * links are ignored everywhere on the page (dragging text into an answer box still works).
 * The native navigation policy in app/shell.py refuses such navigations too.
 */
const IGNORED_TYPES = ['Files', 'text/uri-list'];

export function carriesFilesOrLinks(data: DataTransfer | null): boolean {
  return data !== null && Array.from(data.types).some((type) => IGNORED_TYPES.includes(type));
}

function ignore(event: DragEvent): void {
  if (!carriesFilesOrLinks(event.dataTransfer)) return;
  event.preventDefault();
  event.stopPropagation();
  if (event.dataTransfer) event.dataTransfer.dropEffect = 'none';
}

export function installDropGuard(target: Window = window): void {
  for (const type of ['dragenter', 'dragover', 'drop'] as const) {
    target.addEventListener(type, ignore, { capture: true });
  }
}
