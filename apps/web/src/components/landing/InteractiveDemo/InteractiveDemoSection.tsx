import React from 'react';
import { Sparkles, Play, MousePointer } from 'lucide-react';
import { PageContainer, SectionWrapper } from '../foundation/layout/Container';
import { Heading, Text } from '../foundation/typography/Typography';
import { Badge } from '../foundation/feedback/Badge';
import { SimulatedAppWindow } from './SimulatedAppWindow';
import { FadeUp, ScrollReveal } from '../foundation/motion/MotionWrappers';

export interface InteractiveDemoSectionProps {
  onGetStartedClick?: () => void;
}

export const InteractiveDemoSection: React.FC<InteractiveDemoSectionProps> = ({
  onGetStartedClick,
}) => {
  return (
    <SectionWrapper id="demo" spacing="normal" bg="subtle" className="border-t border-[var(--color-border)]">
      <PageContainer maxWidth="2xl" className="space-y-12">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <FadeUp delay={0.1}>
            <Badge variant="primary" pulse icon={<MousePointer className="w-3.5 h-3.5" />}>
              Interactive Product Experience
            </Badge>
          </FadeUp>

          <FadeUp delay={0.2}>
            <Heading level="h2">
              Try MindMesh Right Now.{' '}
              <span className="text-gradient">No Account Required.</span>
            </Heading>
          </FadeUp>


          <FadeUp delay={0.3}>
            <Text variant="bodyLarge" muted>
              Try searching company files, exploring connected topics, or asking the AI assistant—no signup required.
            </Text>
          </FadeUp>

        </div>

        {/* Live Interactive App Window Simulation */}
        <ScrollReveal threshold={0.1}>
          <SimulatedAppWindow />
        </ScrollReveal>
      </PageContainer>
    </SectionWrapper>
  );
};
