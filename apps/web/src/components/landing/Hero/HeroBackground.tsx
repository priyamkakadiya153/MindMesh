import React from 'react';
import { FloatingElement } from '../foundation/motion/MotionWrappers';

export const HeroBackground: React.FC = () => {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden -z-10">
      {/* Grid Pattern Layer */}
      <div
        className="absolute inset-0 opacity-[0.03] dark:opacity-[0.07]"
        style={{
          backgroundImage: `radial-gradient(var(--color-border) 1px, transparent 1px)`,
          backgroundSize: '32px 32px',
        }}
      />

      {/* Top Ambient Glow Orb - Primary Indigo */}
      <FloatingElement distance={20} duration={8} className="absolute -top-32 left-1/2 -translate-x-1/2">
        <div className="w-[600px] h-[500px] sm:w-[900px] sm:h-[650px] rounded-full bg-gradient-to-tr from-indigo-600/20 via-indigo-500/15 to-purple-600/10 blur-[120px] dark:from-indigo-600/30 dark:via-indigo-500/20 dark:to-purple-600/15 opacity-80" />
      </FloatingElement>

      {/* Left Cyan Highlight Orb */}
      <FloatingElement distance={15} duration={10} className="absolute top-1/4 -left-32">
        <div className="w-[350px] h-[350px] sm:w-[500px] sm:h-[500px] rounded-full bg-cyan-500/15 dark:bg-cyan-500/20 blur-[100px] opacity-70" />
      </FloatingElement>

      {/* Right Violet Glow Orb */}
      <FloatingElement distance={18} duration={9} className="absolute top-1/3 -right-32">
        <div className="w-[350px] h-[350px] sm:w-[550px] sm:h-[550px] rounded-full bg-violet-600/15 dark:bg-violet-600/25 blur-[110px] opacity-70" />
      </FloatingElement>

      {/* Subtle Radial Vignette Fade at Bottom */}
      <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-b from-transparent to-[var(--color-bg)]" />
    </div>
  );
};
