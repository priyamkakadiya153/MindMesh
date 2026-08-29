import React, { useState } from 'react';
import { Network, Sparkles, CheckCircle2, ArrowRight, Share2, Layers } from 'lucide-react';
import { PageContainer, SectionWrapper } from '../foundation/layout/Container';
import { Heading, Text } from '../foundation/typography/Typography';
import { Badge } from '../foundation/feedback/Badge';
import { Button } from '../foundation/buttons/Button';
import { GRAPH_NODES, GRAPH_EDGES } from './graph-dataset';
import { InteractiveGraphCanvas } from './InteractiveGraphCanvas';
import { AIContextPanel } from './AIContextPanel';
import { FadeUp, ScrollReveal } from '../foundation/motion/MotionWrappers';

export interface KnowledgeGraphSectionProps {
  onGetStartedClick?: () => void;
}

export const KnowledgeGraphSection: React.FC<KnowledgeGraphSectionProps> = ({
  onGetStartedClick,
}) => {
  const [selectedNodeId, setSelectedNodeId] = useState<string>('doc-1');
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  const selectedNode =
    GRAPH_NODES.find((n) => n.id === selectedNodeId) || GRAPH_NODES[0];

  return (
    <SectionWrapper id="intelligence" spacing="normal" bg="subtle" className="border-t border-[var(--color-border)]">

      <PageContainer maxWidth="2xl" className="space-y-12">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <FadeUp delay={0.1}>
            <Badge variant="primary" pulse icon={<Network className="w-3.5 h-3.5" />}>
              Living Knowledge Graph Architecture
            </Badge>
          </FadeUp>

          <FadeUp delay={0.2}>
            <Heading level="h2">
              Your Organization's{' '}
              <span className="text-gradient">Living Knowledge Memory.</span>
            </Heading>
          </FadeUp>


          <FadeUp delay={0.3}>
            <Text variant="bodyLarge" muted>
              MindMesh automatically links related documents, team members, and decisions—building an intelligent memory of how your company works.
            </Text>
          </FadeUp>

        </div>

        {/* 2-Column Layout: Left Messaging Panel + Right Interactive Knowledge Graph Canvas */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Feature Highlights & Node Drawer (5 cols) */}
          <div className="lg:col-span-5 space-y-6 text-left">
            <div className="space-y-3">
              <h3 className="font-display font-extrabold text-xl sm:text-2xl text-slate-900 dark:text-white">
                Interconnected Knowledge Graph
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed font-normal">
                Click or hover any node in the graph to inspect how technical specs, chat threads, legal agreements, and team tasks link together in real time.
              </p>
            </div>

            {/* Feature Highlights List */}
            <div className="space-y-2.5">
              {[
                'Automatic relationship discovery & parsing',
                'Graph RAG sub-second citation linking',
                'Cross-workspace intelligence boundaries',
                'Automatic decision extraction graph nodes',
              ].map((feat) => (
                <div key={feat} className="flex items-center gap-2 text-xs font-semibold text-slate-800 dark:text-slate-200">
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  <span>{feat}</span>
                </div>
              ))}
            </div>

            {/* Selected Node Drawer Panel */}
            <AIContextPanel node={selectedNode} />

            <div className="pt-2">
              <Button
                variant="primary"
                size="md"
                rightIcon={<ArrowRight className="w-4 h-4" />}
                onClick={onGetStartedClick}
                className="w-full sm:w-auto font-bold min-h-[48px]"
              >
                Create Your Free Workspace
              </Button>

            </div>
          </div>

          {/* Right Column: Interactive SVG Knowledge Graph Canvas (7 cols) */}
          <div className="lg:col-span-7">
            <InteractiveGraphCanvas
              nodes={GRAPH_NODES}
              edges={GRAPH_EDGES}
              selectedNodeId={selectedNodeId}
              hoveredNodeId={hoveredNodeId}
              onSelectNode={setSelectedNodeId}
              onHoverNode={setHoveredNodeId}
            />
          </div>
        </div>
      </PageContainer>
    </SectionWrapper>
  );
};
