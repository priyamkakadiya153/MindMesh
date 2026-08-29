import React, { useState } from 'react';
import { CreditCard, Sparkles, HelpCircle } from 'lucide-react';
import { PageContainer, SectionWrapper } from '../foundation/layout/Container';
import { Heading, Text } from '../foundation/typography/Typography';
import { Badge } from '../foundation/feedback/Badge';
import { BillingToggle } from './BillingToggle';
import { PricingCardsGrid } from './PricingCardsGrid';
import { EnterpriseContactPanel } from './EnterpriseContactPanel';
import { PricingFAQAccordion } from './PricingFAQAccordion';
import { PricingTier } from './pricing-data';
import { FadeUp, ScrollReveal } from '../foundation/motion/MotionWrappers';

export interface PricingSectionProps {
  onGetStartedClick?: () => void;
}

export const PricingSection: React.FC<PricingSectionProps> = ({
  onGetStartedClick,
}) => {
  const [isYearly, setIsYearly] = useState(true);

  const handleSelectPlan = (tier: PricingTier) => {
    if (onGetStartedClick) {
      onGetStartedClick();
    } else {
      alert(`Selected plan: ${tier.name}`);
    }
  };

  return (
    <SectionWrapper id="pricing" spacing="normal" bg="subtle" className="border-t border-[var(--color-border)]">
      <PageContainer maxWidth="2xl" className="space-y-16">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <FadeUp delay={0.1}>
            <Badge variant="primary" pulse icon={<CreditCard className="w-3.5 h-3.5" />}>
              Transparent Enterprise Pricing
            </Badge>
          </FadeUp>

          <FadeUp delay={0.2}>
            <Heading level="h2">
              Simple Plans{' '}
              <span className="text-gradient">for Teams of Any Size.</span>
            </Heading>
          </FadeUp>


          <FadeUp delay={0.3}>
            <Text variant="bodyLarge" muted>
              Start for free, upgrade your team for shared intelligence, or customize an Enterprise deployment with dedicated SLA guarantees.
            </Text>
          </FadeUp>


          <FadeUp delay={0.4}>
            <BillingToggle isYearly={isYearly} onToggle={setIsYearly} />
          </FadeUp>
        </div>

        {/* 3 Pricing Cards Grid */}
        <ScrollReveal threshold={0.1}>
          <PricingCardsGrid isYearly={isYearly} onSelectPlan={handleSelectPlan} />
        </ScrollReveal>

        {/* Custom Enterprise Deployment Panel */}
        <ScrollReveal threshold={0.1}>
          <EnterpriseContactPanel onContactSales={() => handleSelectPlan({ name: 'Enterprise' } as any)} />
        </ScrollReveal>

        {/* Pricing FAQ Accordion */}
        <ScrollReveal threshold={0.1}>
          <PricingFAQAccordion />
        </ScrollReveal>
      </PageContainer>
    </SectionWrapper>
  );
};
