import React from 'react';
import { XCircle, CheckCircle2, ArrowRight, Sparkles } from 'lucide-react';
import { Card } from '../foundation/layout/Card';
import { Badge } from '../foundation/feedback/Badge';
import { Heading, Text } from '../foundation/typography/Typography';
import { FadeUp } from '../foundation/motion/MotionWrappers';

export interface BeforeAfterPanelProps {
  onGetStartedClick?: () => void;
}

const BEFORE_ITEMS = [
  'Scattered files across Drive, Notion, Slack & local downloads',
  'Critical decisions buried inside forgotten 2 AM chat history',
  'Engineers repeatedly building solutions teammates already built',
  'Keyword search failing on typos, synonyms, and phrasing gaps',
  'New hire onboarding taking 60+ days due to tribal knowledge',
];

const AFTER_ITEMS = [
  'Single, unified vector index for every document, chat & project',
  'Automated decision graph extracting actionable task memory',
  'Instant reuse of organizational research, code & design specs',
  '0.04s natural language semantic search with cited sources',
  'Onboarding reduced to days with grounded AI assistant',
];

export const BeforeAfterPanel: React.FC<BeforeAfterPanelProps> = ({
  onGetStartedClick,
}) => {
  return (
    <FadeUp delay={0.2} className="w-full max-w-5xl mx-auto pt-10">
      <div className="space-y-6 text-center">
        <Badge variant="success" pulse icon={<Sparkles className="w-3.5 h-3.5" />}>
          The MindMesh Transformation
        </Badge>
        <Heading level="h2">Before & After MindMesh</Heading>
        <Text variant="bodyLarge" muted className="max-w-2xl mx-auto">
          See how MindMesh turns fragmented data chaos into structured organizational memory.
        </Text>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 text-left">
          {/* Before Column */}
          <Card
            elevation="soft"
            padding="md"
            hoverLift={false}
            className="border-rose-200/90 dark:border-red-500/30 bg-rose-50/90 dark:bg-red-950/30 text-slate-900 dark:text-white shadow-sm dark:shadow-none"
          >
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-rose-200 dark:border-red-500/20">
              <span className="font-display font-extrabold text-base tracking-wide text-rose-700 dark:text-red-400">
                BEFORE MINDMESH
              </span>
              <Badge variant="error" className="text-[10px]">
                Fragmented Chaos
              </Badge>
            </div>

            <ul className="space-y-3 text-xs text-slate-700 dark:text-slate-300 font-medium">
              {BEFORE_ITEMS.map((item) => (
                <li key={item} className="flex items-start gap-2.5">
                  <XCircle className="w-4 h-4 text-rose-600 dark:text-red-400 shrink-0 mt-0.5" />
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          </Card>

          {/* After Column */}
          <Card
            elevation="medium"
            padding="md"
            hoverLift={false}
            className="border-emerald-300/80 dark:border-emerald-500/40 bg-emerald-50/90 dark:bg-gradient-to-br dark:from-slate-900 dark:via-slate-950 dark:to-emerald-950/30 text-slate-900 dark:text-white shadow-md dark:shadow-ds-glow"
          >
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-emerald-200 dark:border-emerald-500/30">
              <span className="font-display font-extrabold text-base tracking-wide text-emerald-700 dark:text-emerald-400">
                AFTER MINDMESH
              </span>
              <Badge variant="success" className="text-[9px]">
                Unified Memory
              </Badge>
            </div>

            <ul className="space-y-3 text-xs text-slate-800 dark:text-slate-200">
              {AFTER_ITEMS.map((item) => (
                <li key={item} className="flex items-start gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                  <span className="leading-relaxed font-semibold">{item}</span>
                </li>
              ))}
            </ul>
          </Card>
        </div>

      </div>
    </FadeUp>
  );
};
