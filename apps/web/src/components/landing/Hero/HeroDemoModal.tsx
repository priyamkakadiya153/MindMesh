import React, { useState } from 'react';
import { Play, Sparkles, CheckCircle2, Search, FileText, Bot, X } from 'lucide-react';
import { Modal } from '../foundation/feedback/OverlayComponents';
import { Button } from '../foundation/buttons/Button';
import { Badge } from '../foundation/feedback/Badge';
import { Heading, Text } from '../foundation/typography/Typography';

export interface HeroDemoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const TOUR_STEPS = [
  {
    title: 'Natural Language Semantic Search',
    description:
      'Ask complex questions across all past conversations, uploaded files, and meeting notes. Retrieve exact decisions with 0.04s latency.',
    icon: <Search className="w-5 h-5 text-indigo-400" />,
  },
  {
    title: 'Automatic Decision & Task Extraction',
    description:
      'MindMesh continuously monitors discussion threads, automatically extracting actionable tasks and architectural decisions into an organizational knowledge graph.',
    icon: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
  },
  {
    title: 'Grounding AI Assistant',
    description:
      'Generate executive summaries and answer technical queries using 100% cited workspace files with zero data hallucination.',
    icon: <Bot className="w-5 h-5 text-cyan-400" />,
  },
];

export const HeroDemoModal: React.FC<HeroDemoModalProps> = ({ isOpen, onClose }) => {
  const [activeStep, setActiveStep] = useState(0);

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="MindMesh Product Tour"
      description="Experience how MindMesh transforms unstructured communication into organizational memory."
      maxWidth="lg"
    >
      <div className="space-y-6">
        {/* Simulated Video Preview Canvas */}
        <div className="relative aspect-video rounded-ds-xl bg-slate-950 border border-slate-800 overflow-hidden flex flex-col justify-between p-6 shadow-ds-medium">
          <div className="flex items-center justify-between z-10">
            <Badge variant="primary" pulse icon={<Sparkles className="w-3 h-3" />}>
              Live Knowledge Intelligence Tour
            </Badge>
            <span className="text-xs font-mono text-slate-400">Step {activeStep + 1} of 3</span>
          </div>

          <div className="my-auto text-center space-y-3 z-10 max-w-lg mx-auto">
            <div className="w-14 h-14 mx-auto rounded-full bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              {TOUR_STEPS[activeStep].icon}
            </div>
            <h4 className="text-lg font-extrabold text-white">
              {TOUR_STEPS[activeStep].title}
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              {TOUR_STEPS[activeStep].description}
            </p>
          </div>

          <div className="flex items-center justify-center gap-2 z-10">
            {TOUR_STEPS.map((_, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setActiveStep(idx)}
                className={`h-1.5 rounded-full transition-all ${
                  activeStep === idx ? 'w-8 bg-indigo-500' : 'w-2 bg-slate-700 hover:bg-slate-500'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Step Tabs Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {TOUR_STEPS.map((step, idx) => (
            <button
              key={step.title}
              type="button"
              onClick={() => setActiveStep(idx)}
              className={`p-3 rounded-ds-lg border text-left transition-all ${
                activeStep === idx
                  ? 'bg-indigo-500/10 border-indigo-500/40 text-white shadow-ds-soft'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-2 text-xs font-bold mb-1">
                <span>0{idx + 1}.</span>
                <span className="line-clamp-1">{step.title}</span>
              </div>
            </button>
          ))}
        </div>

        {/* Modal Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          <Button variant="ghost" size="sm" onClick={onClose}>
            Close Tour
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              onClose();
              const authEl = document.getElementById('auth-section');
              if (authEl) authEl.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Start Your Free Workspace
          </Button>
        </div>
      </div>
    </Modal>
  );
};
