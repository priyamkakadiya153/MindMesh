import React, { useState } from 'react';
import { HelpCircle, Search, Sparkles } from 'lucide-react';
import { PageContainer, SectionWrapper } from '../foundation/layout/Container';
import { Heading, Text } from '../foundation/typography/Typography';
import { Badge } from '../foundation/feedback/Badge';
import { FAQSearchBar } from './FAQSearchBar';
import { FAQCategoryTabs } from './FAQCategoryTabs';
import { FAQAccordionItem } from './FAQAccordionItem';
import { ContactSupportPanel } from './ContactSupportPanel';
import { FAQ_DATABASE, FAQCategory } from './faq-dataset';
import { FadeUp, ScrollReveal } from '../foundation/motion/MotionWrappers';

export interface FAQSectionProps {
  onGetStartedClick?: () => void;
}

export const FAQSection: React.FC<FAQSectionProps> = ({
  onGetStartedClick,
}) => {
  const [query, setQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<FAQCategory>('getting-started');
  const [openId, setOpenId] = useState<string | null>('gs-1');

  // Filter FAQ items
  const filteredItems = FAQ_DATABASE.filter((item) => {
    const matchesCategory = item.category === activeCategory;
    const matchesQuery =
      !query ||
      item.question.toLowerCase().includes(query.toLowerCase()) ||
      item.answer.toLowerCase().includes(query.toLowerCase());
    return matchesCategory && matchesQuery;
  });


  const handleToggle = (id: string) => {
    setOpenId(openId === id ? null : id);
  };

  return (
    <SectionWrapper id="faq" spacing="normal" bg="base" className="border-t border-[var(--color-border)]">
      <PageContainer maxWidth="2xl" className="space-y-12">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <FadeUp delay={0.1}>
            <Badge variant="primary" pulse icon={<HelpCircle className="w-3.5 h-3.5" />}>
              Frequently Asked Questions
            </Badge>
          </FadeUp>

          <FadeUp delay={0.2}>
            <Heading level="h2">
              Everything You Need to Know{' '}
              <span className="text-gradient">About MindMesh.</span>
            </Heading>
          </FadeUp>


          <FadeUp delay={0.3}>
            <Text variant="bodyLarge" muted>
              Find clear answers about plans, security, AI accuracy, and team setup.
            </Text>
          </FadeUp>

        </div>

        {/* Real-Time Search Bar */}
        <ScrollReveal threshold={0.1}>
          <FAQSearchBar query={query} onQueryChange={setQuery} />
        </ScrollReveal>

        {/* Category Filter Tabs */}
        <ScrollReveal threshold={0.1}>
          <FAQCategoryTabs activeCategory={activeCategory} onSelectCategory={setActiveCategory} />
        </ScrollReveal>

        {/* Accordion Questions List */}
        <ScrollReveal threshold={0.1} className="max-w-3xl mx-auto space-y-3">
          {filteredItems.length > 0 ? (
            filteredItems.map((item) => (
              <FAQAccordionItem
                key={item.id}
                item={item}
                isOpen={openId === item.id}
                onToggle={() => handleToggle(item.id)}
              />
            ))
          ) : (
            <div className="p-8 text-center rounded-ds-xl bg-slate-900/60 border border-slate-800 space-y-2">
              <Search className="w-8 h-8 text-slate-500 mx-auto" />
              <p className="text-sm font-bold text-white">No matching questions found</p>
              <p className="text-xs text-slate-400">
                Try searching for 'pricing', 'security', 'RAG', 'workspaces', or 'SSO'.
              </p>
            </div>
          )}
        </ScrollReveal>

        {/* Contact Support Banner */}
        <ScrollReveal threshold={0.1}>
          <ContactSupportPanel onContactSupport={onGetStartedClick} />
        </ScrollReveal>
      </PageContainer>
    </SectionWrapper>
  );
};
