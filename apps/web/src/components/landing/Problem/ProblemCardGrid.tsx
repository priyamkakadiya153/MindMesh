import React from 'react';
import {
  FolderSearch,
  MessageSquareOff,
  RotateCcw,
  HelpCircle,
  Clock,
  Layers,
  FileWarning,
  BrainCircuit,
} from 'lucide-react';
import { Card } from '../foundation/layout/Card';
import { Badge } from '../foundation/feedback/Badge';
import { Heading, Text } from '../foundation/typography/Typography';
import { StaggerContainer, StaggerItem, CardHover } from '../foundation/motion/MotionWrappers';

export interface ProblemItem {
  id: string;
  icon: React.ReactNode;
  badge: string;
  title: string;
  description: string;
  impactMetric: string;
}

const PROBLEMS: ProblemItem[] = [
  {
    id: 'scattered-docs',
    icon: <FolderSearch className="w-5 h-5 text-red-500" />,
    badge: 'Fragmented Files',
    title: 'Scattered Documents',
    description:
      'Files live across Google Drive, Notion, Slack, and local downloads. Finding the right spec means checking five tools every time.',
    impactMetric: '2.5 hrs wasted daily',
  },
  {
    id: 'lost-conversations',
    icon: <MessageSquareOff className="w-5 h-5 text-amber-500" />,
    badge: 'Burying Decisions',
    title: 'Lost Conversations',
    description:
      'Critical architecture decisions made in 2 AM chat threads disappear down the message history, forcing endless re-discussions.',
    impactMetric: '40% decision loss',
  },
  {
    id: 'repeated-work',
    icon: <RotateCcw className="w-5 h-5 text-orange-500" />,
    badge: 'Duplicated Effort',
    title: 'Repeated Work',
    description:
      'Engineers and designers waste weeks building research and code solutions that a teammate already completed months ago.',
    impactMetric: '3+ weeks lost / quarter',
  },
  {
    id: 'missing-context',
    icon: <HelpCircle className="w-5 h-5 text-yellow-500" />,
    badge: 'Tribal Knowledge',
    title: 'Missing Context',
    description:
      'New team members take months to onboard because institutional knowledge lives inside people’s heads rather than a searchable index.',
    impactMetric: '60-day onboarding lag',
  },
  {
    id: 'slow-search',
    icon: <Clock className="w-5 h-5 text-purple-500" />,
    badge: 'Flawed Tools',
    title: 'Keyword-Only Search',
    description:
      'Legacy search matches exact string characters instead of semantic meaning. Synonyms, typos, or phrasing gaps yield zero results.',
    impactMetric: '70% search failure',
  },
  {
    id: 'knowledge-silos',
    icon: <Layers className="w-5 h-5 text-pink-500" />,
    badge: 'Silo Isolation',
    title: 'Knowledge Silos',
    description:
      'Engineering, Product, and Marketing operate on conflicting versions of specs because documentation is never synchronized.',
    impactMetric: 'Frequent alignment errors',
  },
  {
    id: 'outdated-artifacts',
    icon: <FileWarning className="w-5 h-5 text-rose-500" />,
    badge: 'Version Confusion',
    title: 'Outdated Artifacts',
    description:
      'Nobody knows which document represents the single source of truth, leading to costly deployment and architectural mistakes.',
    impactMetric: 'High error rate',
  },
  {
    id: 'context-burnout',
    icon: <BrainCircuit className="w-5 h-5 text-indigo-500" />,
    badge: 'Focus Interruption',
    title: 'Context-Switch Burnout',
    description:
      'Constantly asking teammates "Where is X?" or jumping between 10 apps to answer simple questions destroys deep engineering focus.',
    impactMetric: 'Fragmented focus state',
  },
];

export const ProblemCardGrid: React.FC = () => {
  return (
    <StaggerContainer
      staggerChildren={0.08}
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mobile-sm:gap-5"
    >
      {PROBLEMS.map((problem) => (
        <StaggerItem key={problem.id}>
          <CardHover className="h-full">
            <Card
              elevation="soft"
              padding="sm"
              hoverLift={false}
              className="h-full flex flex-col justify-between border-slate-200/80 dark:border-slate-800/80 bg-white/60 dark:bg-slate-900/60 hover:border-red-500/30 transition-all duration-300"
            >
              <div className="space-y-3">
                {/* Header Badge & Icon */}
                <div className="flex items-center justify-between">
                  <div className="p-2 rounded-ds-lg bg-red-500/10 dark:bg-red-500/15 shrink-0">
                    {problem.icon}
                  </div>
                  <Badge variant="error" className="text-[10px] py-0 px-2">
                    {problem.badge}
                  </Badge>
                </div>

                {/* Title */}
                <Heading level="h4" className="text-base font-bold text-slate-900 dark:text-white">
                  {problem.title}
                </Heading>

                {/* Description */}
                <Text variant="small" muted className="text-xs leading-relaxed">
                  {problem.description}
                </Text>
              </div>

              {/* Impact Footer */}
              <div className="pt-3 mt-4 border-t border-slate-200/60 dark:border-slate-800/60 flex items-center justify-between text-[11px]">
                <span className="text-slate-400 font-medium">Est. Impact:</span>
                <span className="font-mono font-semibold text-red-600 dark:text-red-400">
                  {problem.impactMetric}
                </span>
              </div>
            </Card>
          </CardHover>
        </StaggerItem>
      ))}
    </StaggerContainer>
  );
};
