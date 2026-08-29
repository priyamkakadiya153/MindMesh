import React from 'react';
import { AlertCircle } from 'lucide-react';
import { PageContainer, SectionWrapper } from '../foundation/layout/Container';
import { Heading, Text } from '../foundation/typography/Typography';
import { Badge } from '../foundation/feedback/Badge';
import { Divider } from '../foundation/feedback/OverlayComponents';
import { ProblemCardGrid } from './ProblemCardGrid';
import { DisconnectedKnowledgeIllustration } from './DisconnectedKnowledgeIllustration';
import { SolutionTransitionBanner } from './SolutionTransitionBanner';
import { FadeUp, ScrollReveal } from '../foundation/motion/MotionWrappers';

export interface ProblemSectionProps {
  onExploreSolutionClick?: () => void;
}

export const ProblemSection: React.FC<ProblemSectionProps> = ({
  onExploreSolutionClick,
}) => {
  return (
    <SectionWrapper id="problem" spacing="normal" bg="subtle" className="border-t border-[var(--color-border)]">
      <PageContainer maxWidth="2xl" className="space-y-16">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <FadeUp delay={0.1}>
            <Badge variant="error" icon={<AlertCircle className="w-3.5 h-3.5" />}>
              The Everyday Knowledge Problem
            </Badge>
          </FadeUp>

          <FadeUp delay={0.2}>
            <Heading level="h2">
              Knowledge is everywhere. But{' '}
              <span className="text-gradient">nobody can find it.</span>
            </Heading>
          </FadeUp>


          <FadeUp delay={0.3}>
            <Text variant="bodyLarge" muted>
              Important decisions get lost in chat threads. Documents get buried in cloud drives. MindMesh gives your team instant access to past knowledge.
            </Text>
          </FadeUp>

        </div>

        {/* 8 Pain Point Problem Cards Grid */}
        <ScrollReveal threshold={0.1}>
          <ProblemCardGrid />
        </ScrollReveal>

        <Divider gradient className="my-12" />

        {/* Interactive Disconnected vs Connected Knowledge Illustration */}
        <ScrollReveal threshold={0.1}>
          <DisconnectedKnowledgeIllustration />
        </ScrollReveal>

        {/* Transition into MindMesh Solution */}
        <SolutionTransitionBanner onExploreClick={onExploreSolutionClick} />
      </PageContainer>
    </SectionWrapper>
  );
};
