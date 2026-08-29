/**
 * MindMesh Design System Token Registry
 * Scalable, production-ready tokens for typography, spacing, colors, shadows, radius, and motion.
 */

export const TYPOGRAPHY_SCALE = {
  display: 'var(--font-display)',
  h1: 'var(--font-h1)',
  h2: 'var(--font-h2)',
  h3: 'var(--font-h3)',
  h4: 'var(--font-h4)',
  bodyLarge: 'var(--font-body-lg)',
  body: 'var(--font-body)',
  small: 'var(--font-sm)',
  caption: 'var(--font-caption)',
} as const;

export const SPACING_SCALE = {
  xs: 'var(--space-xs)',
  sm: 'var(--space-sm)',
  md: 'var(--space-md)',
  lg: 'var(--space-lg)',
  xl: 'var(--space-xl)',
  '2xl': 'var(--space-2xl)',
  '3xl': 'var(--space-3xl)',
} as const;

export const RADIUS_SYSTEM = {
  sm: 'var(--radius-sm)',
  md: 'var(--radius-md)',
  lg: 'var(--radius-lg)',
  xl: 'var(--radius-xl)',
  pill: 'var(--radius-pill)',
} as const;

export const SHADOW_SYSTEM = {
  soft: 'var(--shadow-soft)',
  medium: 'var(--shadow-medium)',
  floating: 'var(--shadow-floating)',
  modal: 'var(--shadow-modal)',
  hero: 'var(--shadow-hero)',
} as const;

export const COLOR_TOKENS = {
  primary: 'var(--color-primary)',
  primaryHover: 'var(--color-primary-hover)',
  primaryLight: 'var(--color-primary-light)',
  secondary: 'var(--color-secondary)',
  accent: 'var(--color-accent)',
  surface: 'var(--color-surface)',
  surfaceHover: 'var(--color-surface-hover)',
  surfaceGlass: 'var(--color-surface-glass)',
  background: 'var(--color-bg)',
  border: 'var(--color-border)',
  textPrimary: 'var(--color-text-primary)',
  textSecondary: 'var(--color-text-secondary)',
  textMuted: 'var(--color-text-muted)',
  success: 'var(--color-success)',
  warning: 'var(--color-warning)',
  error: 'var(--color-error)',
  info: 'var(--color-info)',
} as const;

export const GRADIENTS = {
  hero: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(79, 70, 229, 0.05) 50%, rgba(0, 0, 0, 0) 100%)',
  heroDark: 'linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(129, 140, 248, 0.08) 50%, rgba(11, 15, 25, 0) 100%)',
  primaryButton: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
  accentGlow: 'radial-gradient(circle at center, rgba(99, 102, 241, 0.25) 0%, rgba(99, 102, 241, 0) 70%)',
  glassCard: 'linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%)',
} as const;

export const TARGET_BREAKPOINTS = {
  mobileXs: 375,
  mobileSm: 390,
  mobileMd: 412,
  mobileLg: 430,
  tablet: 768,
  desktop: 1024,
  wideDesktop: 1280,
} as const;
