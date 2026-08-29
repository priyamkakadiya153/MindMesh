import React from 'react';
import { ArrowRight, Sparkles, CheckCircle2 } from 'lucide-react';
import { Button } from '../foundation/buttons/Button';
import { Badge } from '../foundation/feedback/Badge';
import { Heading, Text } from '../foundation/typography/Typography';
import { FadeUp } from '../foundation/motion/MotionWrappers';

export interface SolutionTransitionBannerProps {
  onExploreClick?: () => void;
}

export const SolutionTransitionBanner: React.FC<SolutionTransitionBannerProps> = ({
  onExploreClick,
}) => {
  return (
    <FadeUp delay={0.2} className="w-full max-w-4xl mx-auto pt-8">
      <div className="relative p-8 sm:p-10 rounded-ds-2xl bg-gradient-to-br from-indigo-50/90 via-white to-purple-50/90 dark:from-indigo-900/40 dark:via-slate-900/80 dark:to-slate-950 border border-indigo-200 dark:border-indigo-500/30 shadow-ds-hero text-center space-y-6 overflow-hidden">
        {/* Glow Ambient Orb */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none" />

        <Badge variant="primary" pulse icon={<Sparkles className="w-3.5 h-3.5" />}>
          The MindMesh Solution
        </Badge>

        <Heading level="h2" className="max-w-2xl mx-auto text-slate-900 dark:text-white font-extrabold">
          Turn Disconnected Chaos into Unified Intelligence.
        </Heading>

        <Text variant="bodyLarge" muted className="max-w-xl mx-auto">
          MindMesh replaces scattered search checking with a single, grounded AI system that knows every file, conversation, decision, and project in your organization.
        </Text>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl mx-auto text-left text-xs text-slate-900 dark:text-slate-200 pt-2">
          <div className="flex items-center gap-2 p-3 rounded-ds-lg bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>0.04s Instant Vector Search</span>
          </div>
          <div className="flex items-center gap-2 p-3 rounded-ds-lg bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>Automatic Decision Graph</span>
          </div>
          <div className="flex items-center gap-2 p-3 rounded-ds-lg bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>Zero Data Hallucinations</span>
          </div>
        </div>


        <div className="pt-2">
          <Button
            variant="primary"
            size="lg"
            rightIcon={<ArrowRight className="w-5 h-5" />}
            onClick={onExploreClick}
          >
            Explore How MindMesh Works
          </Button>
        </div>
      </div>
    </FadeUp>
  );
};
