import { Variants } from 'framer-motion';

/**
 * Standard Easing Curves
 */
export const EASINGS = {
  smooth: [0.25, 0.1, 0.25, 1.0],
  bounce: [0.34, 1.56, 0.64, 1],
  spring: [0.175, 0.885, 0.32, 1.275],
  outExpo: [0.19, 1, 0.22, 1],
} as const;

/**
 * Motion Variants Library
 */
export const fadeInVariants: Variants = {
  hidden: { opacity: 0 },
  visible: (custom = { duration: 0.3, delay: 0 }) => ({
    opacity: 1,
    transition: {
      duration: Math.min(custom.duration || 0.3, 0.4),
      delay: custom.delay || 0,
      ease: EASINGS.outExpo,
    },
  }),
};

export const fadeUpVariants: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: (custom = { duration: 0.35, delay: 0 }) => ({
    opacity: 1,
    y: 0,
    transition: {
      duration: Math.min(custom.duration || 0.35, 0.4),
      delay: custom.delay || 0,
      ease: EASINGS.outExpo,
    },
  }),
};

export const fadeDownVariants: Variants = {
  hidden: { opacity: 0, y: -16 },
  visible: (custom = { duration: 0.35, delay: 0 }) => ({
    opacity: 1,
    y: 0,
    transition: {
      duration: Math.min(custom.duration || 0.35, 0.4),
      delay: custom.delay || 0,
      ease: EASINGS.outExpo,
    },
  }),
};

export const fadeLeftVariants: Variants = {
  hidden: { opacity: 0, x: -20 },
  visible: (custom = { duration: 0.35, delay: 0 }) => ({
    opacity: 1,
    x: 0,
    transition: {
      duration: Math.min(custom.duration || 0.35, 0.4),
      delay: custom.delay || 0,
      ease: EASINGS.outExpo,
    },
  }),
};

export const fadeRightVariants: Variants = {
  hidden: { opacity: 0, x: 20 },
  visible: (custom = { duration: 0.35, delay: 0 }) => ({
    opacity: 1,
    x: 0,
    transition: {
      duration: Math.min(custom.duration || 0.35, 0.4),
      delay: custom.delay || 0,
      ease: EASINGS.outExpo,
    },
  }),
};

export const scaleInVariants: Variants = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: (custom = { duration: 0.35, delay: 0 }) => ({
    opacity: 1,
    scale: 1,
    transition: {
      duration: Math.min(custom.duration || 0.35, 0.4),
      delay: custom.delay || 0,
      ease: EASINGS.outExpo,
    },
  }),
};

export const blurRevealVariants: Variants = {
  hidden: { opacity: 0, filter: 'blur(8px)', y: 12 },
  visible: (custom = { duration: 0.35, delay: 0 }) => ({
    opacity: 1,
    filter: 'blur(0px)',
    y: 0,
    transition: {
      duration: Math.min(custom.duration || 0.35, 0.4),
      delay: custom.delay || 0,
      ease: EASINGS.outExpo,
    },
  }),
};

export const staggerContainerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: (custom = { staggerChildren: 0.06, delayChildren: 0 }) => ({
    opacity: 1,
    transition: {
      staggerChildren: Math.min(custom.staggerChildren || 0.06, 0.1),
      delayChildren: custom.delayChildren || 0,
    },
  }),
};

export const staggerItemVariants: Variants = {
  hidden: { opacity: 0, y: 14 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.35,
      ease: EASINGS.outExpo,
    },
  },
};

