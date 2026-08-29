import React from 'react';
import { motion, useReducedMotion, HTMLMotionProps } from 'framer-motion';
import {
  fadeInVariants,
  fadeUpVariants,
  fadeDownVariants,
  fadeLeftVariants,
  fadeRightVariants,
  scaleInVariants,
  blurRevealVariants,
  staggerContainerVariants,
  staggerItemVariants,
} from './motion-utils';

export interface BaseMotionProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode;
  duration?: number;
  delay?: number;
  className?: string;
}

export const FadeIn: React.FC<BaseMotionProps> = ({
  children,
  duration = 0.3,
  delay = 0,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      variants={fadeInVariants}
      initial="hidden"
      animate="visible"
      custom={{ duration, delay }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const FadeUp: React.FC<BaseMotionProps> = ({
  children,
  duration = 0.35,
  delay = 0,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      variants={fadeUpVariants}
      initial="hidden"
      animate="visible"
      custom={{ duration, delay }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const FadeDown: React.FC<BaseMotionProps> = ({
  children,
  duration = 0.35,
  delay = 0,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      variants={fadeDownVariants}
      initial="hidden"
      animate="visible"
      custom={{ duration, delay }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const FadeLeft: React.FC<BaseMotionProps> = ({
  children,
  duration = 0.35,
  delay = 0,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      variants={fadeLeftVariants}
      initial="hidden"
      animate="visible"
      custom={{ duration, delay }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const FadeRight: React.FC<BaseMotionProps> = ({
  children,
  duration = 0.35,
  delay = 0,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      variants={fadeRightVariants}
      initial="hidden"
      animate="visible"
      custom={{ duration, delay }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const ScaleIn: React.FC<BaseMotionProps> = ({
  children,
  duration = 0.35,
  delay = 0,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;


  return (
    <motion.div
      variants={scaleInVariants}
      initial="hidden"
      animate="visible"
      custom={{ duration, delay }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const BlurReveal: React.FC<BaseMotionProps> = ({
  children,
  duration = 0.7,
  delay = 0,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      variants={blurRevealVariants}
      initial="hidden"
      animate="visible"
      custom={{ duration, delay }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export interface ScrollRevealProps extends BaseMotionProps {
  threshold?: number;
  once?: boolean;
}

export const ScrollReveal: React.FC<ScrollRevealProps> = ({
  children,
  duration = 0.6,
  delay = 0,
  threshold = 0.15,
  once = true,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      variants={fadeUpVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount: threshold }}
      custom={{ duration, delay }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export interface StaggerContainerProps extends BaseMotionProps {
  staggerChildren?: number;
  delayChildren?: number;
  viewportOnce?: boolean;
}

export const StaggerContainer: React.FC<StaggerContainerProps> = ({
  children,
  staggerChildren = 0.08,
  delayChildren = 0,
  viewportOnce = true,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      variants={staggerContainerVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: viewportOnce, amount: 0.1 }}
      custom={{ staggerChildren, delayChildren }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const StaggerItem: React.FC<BaseMotionProps> = ({
  children,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div variants={staggerItemVariants} className={className} {...props}>
      {children}
    </motion.div>
  );
};

export const HoverLift: React.FC<BaseMotionProps & { liftDistance?: number }> = ({
  children,
  liftDistance = -4,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      whileHover={{ y: liftDistance, transition: { duration: 0.2, ease: 'easeOut' } }}
      whileTap={{ y: 0 }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const CardHover: React.FC<BaseMotionProps> = ({
  children,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      whileHover={{
        y: -6,
        scale: 1.01,
        transition: { duration: 0.25, ease: [0.19, 1, 0.22, 1] },
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const FloatingElement: React.FC<BaseMotionProps & { distance?: number; duration?: number }> = ({
  children,
  distance = 12,
  duration = 5,
  className = '',
  ...props
}) => {
  const shouldReduceMotion = useReducedMotion();
  if (shouldReduceMotion) return <div className={className}>{children}</div>;

  return (
    <motion.div
      animate={{
        y: [0, -distance, 0],
      }}
      transition={{
        duration,
        repeat: Infinity,
        repeatType: 'reverse',
        ease: 'easeInOut',
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};
