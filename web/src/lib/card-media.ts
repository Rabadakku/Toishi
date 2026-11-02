import { getPractice } from './practice-api';
import type { CardMedia } from './types';

/**
 * Where the media of a card come from (ADR-0017). Python serves them from this page's own
 * origin (`/media/...`, app/media.py) and `library_card_media` says which URL each reference
 * in the card's text stands for. The answers are cached per card for the life of the page.
 */

/** A reference as the card writes it -> a URL on this origin, or null when it has none. */
export type MediaResolver = (ref: string) => string | null;

/** Study.svelte provides this so the text drawn inside it knows whose media it shows. */
export const CARD_CONTEXT = Symbol('toishi.card');

export interface CardContext {
  readonly cardId: string | null;
}

/** The only URLs a card may load: the two shapes app/media.py serves, nothing else. */
const MEDIA_URL = /^\/media\/(?:user\/[0-9a-f]{64}(?:\.[a-z0-9]{1,8})?|pack\/[a-z0-9][a-z0-9._-]*\/[^?#\\]+)$/;

export type MediaMap = ReadonlyMap<string, string>;

const loaded = new Map<string, MediaMap>();
const pending = new Map<string, Promise<MediaMap>>();
const NONE: MediaMap = new Map();

function toMap(media: CardMedia): MediaMap {
  const files = new Map<string, string>();
  for (const [ref, url] of Object.entries(media.files ?? {})) {
    if (typeof url === 'string' && MEDIA_URL.test(url)) files.set(ref, url);
  }
  return files;
}

/** The media of a card already fetched, else undefined (no waiting). */
export function peekCardMedia(cardId: string): MediaMap | undefined {
  return loaded.get(cardId);
}

/** Fetch (once) the media of a card. A failed call answers "no media" and is tried again later. */
export function loadCardMedia(cardId: string): Promise<MediaMap> {
  const known = loaded.get(cardId);
  if (known) return Promise.resolve(known);
  let request = pending.get(cardId);
  if (!request) {
    request = getPractice()
      .then(({ api }) => api.library_card_media({ card_id: cardId }))
      .then((media) => {
        const files = toMap(media);
        loaded.set(cardId, files);
        return files;
      })
      .catch(() => NONE)
      .finally(() => pending.delete(cardId));
    pending.set(cardId, request);
  }
  return request;
}

/** Look up a reference; Markdown percent-encodes what it reads, so the decoded form counts too. */
export function mediaResolver(files: MediaMap | null | undefined): MediaResolver {
  return (ref) => {
    if (!files) return null;
    const direct = files.get(ref);
    if (direct !== undefined) return direct;
    try {
      return files.get(decodeURI(ref)) ?? null;
    } catch {
      return null; // a malformed escape
    }
  };
}
