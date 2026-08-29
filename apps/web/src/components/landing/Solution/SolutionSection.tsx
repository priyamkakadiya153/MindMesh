import React, { useState } from 'react';
import { Sparkles, Layers } from 'lucide-react';
import { PageContainer, SectionWrapper } from '../foundation/layout/Container';
import { Heading, Text } from '../foundation/typography/Typography';
import { Badge } from '../foundation/feedback/Badge';
import { Divider } from '../foundation/feedback/OverlayComponents';
import { KnowledgePipeline } from './KnowledgePipeline';
import { SolutionCardList } from './SolutionCardList';
import { BeforeAfterPanel } from './BeforeAfterPanel';
import { FadeUp, ScrollReveal } from '../foundation/motion/MotionWrappers';

export interface SolutionSectionProps {
  onGetStartedClick?: () => void;
}

export const SolutionSection: React.FC<SolutionSectionProps> = ({
  onGetStartedClick,
}) => {
  const [activeStep, setActiveStep] = useState(1);

  return (
    <SectionWrapper id="how-it-works" spacing="normal" bg="base" className="border-t border-[var(--color-border)]">

      <PageContainer maxWidth="2xl" className="space-y-16">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <FadeUp delay={0.1}>
            <Badge variant="primary" pulse icon={<Sparkles className="w-3.5 h-3.5" />}>
              The MindMesh Knowledge Pipeline
            </Badge>
          </FadeUp>

          <FadeUp delay={0.2}>
            <Heading level="h2">
              How MindMesh Transforms Scattered Data{' '}
              <span className="text-gradient">into Memory.</span>
            </Heading>
          </FadeUp>


          <FadeUp delay={0.3}>
            <Text variant="bodyLarge" muted>
              MindMesh automatically indexes files and team chats, linking related ideas so anyone can find past decisions instantly.
            </Text>
          </FadeUp>

        </div>

        {/* 5-Step Animated Knowledge Pipeline Stepper */}
        <ScrollReveal threshold={0.1}>
          <KnowledgePipeline activeStep={activeStep} onSelectStep={setActiveStep} />
        </ScrollReveal>

        {/* Interactive Active Stage Card Display */}
        <ScrollReveal threshold={0.1}>
          <SolutionCardList activeStep={activeStep} onSelectStep={setActiveStep} />
        </ScrollReveal>

        <Divider gradient className="my-12" />

        {/* Before vs After Transformation Matrix */}
        <ScrollReveal threshold={0.1}>
          <BeforeAfterPanel onGetStartedClick={onGetStartedClick} />
        </ScrollReveal>
      </PageContainer>
    </SectionWrapper>
  );
};
