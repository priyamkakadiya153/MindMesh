import React, { useState } from 'react';
import { Layers, Sparkles, ArrowRight } from 'lucide-react';
import { PageContainer, SectionWrapper } from '../foundation/layout/Container';
import { Heading, Text } from '../foundation/typography/Typography';
import { Badge } from '../foundation/feedback/Badge';
import { Button } from '../foundation/buttons/Button';
import { FEATURE_CATEGORIES } from './feature-data';
import { FeatureCategoryAccordion } from './FeatureCategoryAccordion';
import { FeatureIllustration } from './FeatureIllustration';
import { FadeUp, ScrollReveal } from '../foundation/motion/MotionWrappers';

export interface FeaturesSectionProps {
  onGetStartedClick?: () => void;
}

export const FeaturesSection: React.FC<FeaturesSectionProps> = ({
  onGetStartedClick,
}) => {
  const [expandedCategoryId, setExpandedCategoryId] = useState<string>('ai-intelligence');

  const activeCategory =
    FEATURE_CATEGORIES.find((c) => c.id === expandedCategoryId) || FEATURE_CATEGORIES[0];

  const handleToggleCategory = (id: string) => {
    // If clicking already open category, keep it open (or toggle)
    setExpandedCategoryId(id);
  };

  return (
    <SectionWrapper id="features" spacing="normal" bg="subtle" className="border-t border-[var(--color-border)]">
      <PageContainer maxWidth="2xl" className="space-y-16">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <FadeUp delay={0.1}>
            <Badge variant="primary" pulse icon={<Layers className="w-3.5 h-3.5" />}>
              Complete Knowledge Capabilities
            </Badge>
          </FadeUp>

          <FadeUp delay={0.2}>
            <Heading level="h2">
              Explore the MindMesh{' '}
              <span className="text-gradient">Platform Capabilities.</span>
            </Heading>
          </FadeUp>


          <FadeUp delay={0.3}>
            <Text variant="bodyLarge" muted>
              Everything your team needs to capture, organize, and search company knowledge in one place.
            </Text>
          </FadeUp>

        </div>

        {/* 7 Feature Categories & Illustration Split Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: 7 Expandable Category Accordions (7 cols) */}
          <div className="lg:col-span-7 space-y-3">
            {FEATURE_CATEGORIES.map((cat) => (
              <FeatureCategoryAccordion
                key={cat.id}
                category={cat}
                isExpanded={expandedCategoryId === cat.id}
                onToggle={() => handleToggleCategory(cat.id)}
              />
            ))}
          </div>

          {/* Right Column: Dynamic Live Feature Illustration (5 cols) */}
          <div className="lg:col-span-5 sticky top-28 hidden lg:block">
            <FeatureIllustration category={activeCategory} />
          </div>
        </div>
      </PageContainer>
    </SectionWrapper>
  );
};


