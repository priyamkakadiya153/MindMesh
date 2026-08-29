export function applyOrganizationAccentColor(color?: string | null) {
  const hex = color && /^#[0-9A-Fa-f]{6}$/.test(color) ? color : '#3B82F6';
  const root = document.documentElement;

  root.style.setProperty('--accent', hex);
  root.style.setProperty('--accent-hover', adjustColorBrightness(hex, -15));
  root.style.setProperty('--accent-subtle', `${hex}20`);
  root.style.setProperty('--accent-text', hex);
  root.style.setProperty('--border-focus', hex);
}

function adjustColorBrightness(hex: string, percent: number): string {
  let num = parseInt(hex.replace('#', ''), 16);
  let r = (num >> 16) + Math.round(2.55 * percent);
  let g = ((num >> 8) & 0x00FF) + Math.round(2.55 * percent);
  let b = (num & 0x0000FF) + Math.round(2.55 * percent);

  r = Math.min(255, Math.max(0, r));
  g = Math.min(255, Math.max(0, g));
  b = Math.min(255, Math.max(0, b));

  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
}
