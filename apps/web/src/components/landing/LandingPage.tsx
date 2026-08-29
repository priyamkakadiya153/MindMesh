import React, { useState } from 'react';
import { LandingNavbar } from './foundation/navigation/LandingNavbar';
import { LandingFooter } from './foundation/navigation/LandingFooter';

import { HeroSection } from './Hero/HeroSection';
import { ProblemSection } from './Problem/ProblemSection';
import { KnowledgeGraphSection } from './KnowledgeGraph/KnowledgeGraphSection';
import { SolutionSection } from './Solution/SolutionSection';
import { InteractiveDemoSection } from './InteractiveDemo/InteractiveDemoSection';
import { FeaturesSection } from './Features/FeaturesSection';
import { PricingSection } from './Pricing/PricingSection';
import { FAQSection } from './FAQ/FAQSection';

import { Modal } from './foundation/feedback/OverlayComponents';
import { Button } from './foundation/buttons/Button';
import { Text } from './foundation/typography/Typography';
import { ArrowRight } from 'lucide-react';

export interface LandingPageProps {
  onSignInClick?: () => void;
  onGetStartedClick?: () => void;
}

export const LandingPage: React.FC<LandingPageProps> = ({
  onSignInClick,
  onGetStartedClick,
}) => {
  const [isGetStartedModalOpen, setIsGetStartedModalOpen] = useState(false);

  const handleGetStarted = () => {
    if (onGetStartedClick) {
      onGetStartedClick();
    } else {
      setIsGetStartedModalOpen(true);
    }
  };

  return (
    <div className="min-h-screen bg-[var(--color-bg)] text-[var(--color-text-primary)] transition-colors duration-300">
      {/* Foundational Navigation Bar */}
      <LandingNavbar
        onSignInClick={onSignInClick}
        onGetStartedClick={handleGetStarted}
      />

      {/* Main Content Landmark */}
      <main id="main-content" className="relative">
        {/* 1. Hero Section */}
        <HeroSection onGetStartedClick={handleGetStarted} />

        {/* 2. Problem Section */}
        <ProblemSection onExploreSolutionClick={handleGetStarted} />

        {/* 3. Before vs After — Interactive Knowledge Graph */}
        <KnowledgeGraphSection onGetStartedClick={handleGetStarted} />

        {/* 4. How MindMesh Works — Knowledge Lifecycle Pipeline */}
        <SolutionSection onGetStartedClick={handleGetStarted} />

        {/* 5. Interactive Product Sandbox Demo */}
        <InteractiveDemoSection onGetStartedClick={handleGetStarted} />

        {/* 6. AI Features & Platform Capabilities */}
        <FeaturesSection onGetStartedClick={handleGetStarted} />

        {/* 7. Transparent Pricing Tiers */}
        <PricingSection onGetStartedClick={handleGetStarted} />

        {/* 8. Frequently Asked Questions & Final CTA */}
        <FAQSection onGetStartedClick={handleGetStarted} />
      </main>


      {/* Premium SaaS Footer */}
      <LandingFooter
        onSignInClick={onSignInClick}
        onGetStartedClick={handleGetStarted}
      />




      {/* Get Started Registration Modal */}
      <Modal
        isOpen={isGetStartedModalOpen}
        onClose={() => setIsGetStartedModalOpen(false)}
        title="Start Your MindMesh Workspace"
        description="Create an AI-powered organizational memory for your team in under 60 seconds."
      >
        <div className="space-y-4 text-left">
          <Text variant="body">
            Get instant semantic search across all your team's chats, documents, and decisions.
          </Text>

          <div className="p-4 rounded-ds-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-mono space-y-1">
            <div>✓ Unlimited Semantic Vector Queries</div>
            <div>✓ SOC2 Compliant & AES-256 Encrypted</div>
            <div>✓ Grounded AI Assistant with Source Citations</div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <Button variant="outline" size="sm" onClick={() => setIsGetStartedModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              rightIcon={<ArrowRight className="w-4 h-4" />}
              onClick={() => {
                setIsGetStartedModalOpen(false);
                if (onSignInClick) onSignInClick();
              }}
            >
              Proceed to Sign Up
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
