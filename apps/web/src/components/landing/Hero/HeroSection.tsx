import React, { useState } from 'react';
import { Sparkles, ArrowRight, Play } from 'lucide-react';
import { HeroBackground } from './HeroBackground';
import { HeroTrustIndicators } from './HeroTrustIndicators';
import { HeroDashboardPreview } from './HeroDashboardPreview';
import { HeroFloatingCardsDesktop, HeroFloatingCardsMobile } from './HeroFloatingCards';
import { HeroDemoModal } from './HeroDemoModal';
import { PageContainer, SectionWrapper } from '../foundation/layout/Container';
import { Heading, Text } from '../foundation/typography/Typography';
import { Button } from '../foundation/buttons/Button';
import { Badge } from '../foundation/feedback/Badge';
import {
  FadeUp,
  BlurReveal,
  ScaleIn,
  FadeIn,
  StaggerContainer,
  StaggerItem,
} from '../foundation/motion/MotionWrappers';

export interface HeroSectionProps {
  onGetStartedClick?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onGetStartedClick }) => {
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);

  return (
    <SectionWrapper id="hero" spacing="compact" className="pt-16 mobile-lg:pt-20 lg:pt-24 pb-12">
      {/* Background Orbs & Grid */}
      <HeroBackground />

      <PageContainer maxWidth="2xl">
        <div className="relative z-10 flex flex-col items-center text-center space-y-6">
          {/* Staggered Motion Entrance Sequence */}
          <StaggerContainer staggerChildren={0.1} className="flex flex-col items-center text-center space-y-5 max-w-4xl mx-auto">
            {/* 1. Category Badge */}
            <StaggerItem>
              <Badge variant="primary" pulse icon={<Sparkles className="w-3.5 h-3.5" />}>
                AI-Powered Knowledge Intelligence System
              </Badge>
            </StaggerItem>

            {/* 2. Headline */}
            <StaggerItem>
              <Heading level="display" className="max-w-4xl font-extrabold tracking-tight">
                Your Team’s Knowledge.{' '}
                <span className="text-gradient">Instantly Searchable.</span>
              </Heading>
            </StaggerItem>

            {/* 3. Supporting Text */}
            <StaggerItem>
              <Text variant="bodyLarge" muted className="max-w-2xl mx-auto text-slate-700 dark:text-slate-300 font-medium">
                MindMesh connects your team’s documents, chats, and decisions into a single searchable workspace. Ask questions in plain English and get instant answers with exact source links.
              </Text>
            </StaggerItem>


            {/* 4. Prominent CTAs */}
            <StaggerItem className="w-full sm:w-auto">
              <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 w-full sm:w-auto pt-2">
                <Button
                  variant="primary"
                  size="lg"
                  fullWidth={true}
                  rightIcon={<ArrowRight className="w-5 h-5" />}
                  onClick={onGetStartedClick}
                  className="w-full sm:w-auto min-h-[48px] px-8 py-3.5 text-base font-bold bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-[0_0_25px_rgba(99,102,241,0.45)] transition-all duration-300 transform hover:scale-[1.02]"
                >
                  Start Free Workspace — 60s Setup
                </Button>

                <Button
                  variant="outline"
                  size="lg"
                  fullWidth={true}
                  leftIcon={<Play className="w-4 h-4 text-indigo-400 fill-indigo-400/20" />}
                  onClick={() => setIsDemoModalOpen(true)}
                  className="w-full sm:w-auto min-h-[48px] px-6 py-3.5 text-base font-semibold border-slate-700 hover:border-slate-500"
                >
                  Watch Demo Video
                </Button>
              </div>
            </StaggerItem>


            {/* 5. Enhanced Trust Proof Chips */}
            <StaggerItem className="w-full pt-1">
              <div className="flex flex-wrap items-center justify-center gap-4 text-xs font-semibold text-slate-400 font-mono">
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  SOC2 Type II Certified
                </span>
                <span className="text-slate-600">•</span>
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                  0.04s Vector Lookup
                </span>
                <span className="text-slate-600">•</span>
                <span className="flex items-center gap-1.5 text-slate-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                  No Credit Card Required
                </span>
              </div>
            </StaggerItem>

            {/* 6. Company Trust Badges */}
            <StaggerItem className="w-full pt-2">
              <HeroTrustIndicators />
            </StaggerItem>
          </StaggerContainer>

          {/* 7. Interactive Dashboard Preview Mockup */}
          <div className="relative w-full max-w-5xl mx-auto pt-6">
            <ScaleIn duration={0.7} delay={0.3}>
              <HeroDashboardPreview />
            </ScaleIn>

            {/* Absolute Floating UI Badges (Desktop) */}
            <HeroFloatingCardsDesktop />

            {/* Compact Feature Grid (Mobile) */}
            <HeroFloatingCardsMobile />
          </div>
        </div>
      </PageContainer>

      {/* Interactive Demo Tour Modal */}
      <HeroDemoModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
      />
    </SectionWrapper>
  );
};

