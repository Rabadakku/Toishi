/** 24x24 stroke icons. Each is a list of SVG path strings; drawn in currentColor. */
const CIRCLE = 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Z';

export const ICONS = {
  check: ['M20 6 9 17l-5-5'],
  'check-circle': [CIRCLE, 'm8 12 3 3 5-6'],
  'x-circle': [CIRCLE, 'm9 9 6 6M15 9l-6 6'],
  pause: ['M8 5v14M16 5v14'],
  play: ['M8 5v14l11-7Z'],
  help: [CIRCLE, 'M9.6 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1.1.9-1.1 1.7', 'M12 17h.01'],
  calculator: ['M6 3h12a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z', 'M8 7h8', 'M8.5 12h.01M12 12h.01M15.5 12h.01M8.5 16h.01M12 16h.01M15.5 16h.01'],
  home: ['M4 11 12 4l8 7', 'M6 10v10h12V10'],
  study: ['M4 20l4-1 11-11-3-3L5 16l-1 4Z', 'm14 6 3 3'],
  library: ['M5 4h4v16H5Z', 'M11 4h4v16h-4Z', 'm16.5 5.5 3.5 1-3.5 13.5-3.5-1Z'],
  browse: ['M4 4h7v7H4ZM13 4h7v7h-7ZM4 13h7v7H4ZM13 13h7v7h-7Z'],
  stats: ['M5 20V10M12 20V4M19 20v-7'],
  settings: ['M4 7h8M18 7h2M4 17h2M12 17h8', 'M15 5a2 2 0 1 0 0 4 2 2 0 0 0 0-4ZM9 15a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z'],
  keyboard: ['M3 6h18v12H3Z', 'M7 10h.01M11 10h.01M15 10h.01M7 14h10'],
  'arrow-right': ['M5 12h14M13 6l6 6-6 6'],
  info: [CIRCLE, 'M12 11v5M12 8h.01'],
  alert: ['M12 4 3 20h18L12 4Z', 'M12 10v4M12 17h.01'],
  focus: ['M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5'],
  unfocus: ['M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5'],
  hint: ['M9 18h6M10 21h4', 'M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3Z'],
  undo: ['M9 14 4 9l5-5', 'M4 9h10a6 6 0 0 1 0 12h-3'],
  flag: ['M5 21V4', 'M5 4h12l-2 4 2 4H5'],
  text: ['M5 6V4h14v2M12 4v16M9 20h6'],
  math: ['M18 5H6l6 7-6 7h12'],
} as const;

export type IconName = keyof typeof ICONS;
