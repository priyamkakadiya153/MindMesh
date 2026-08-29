import React from 'react';
import { HelpCircle, ArrowRight, MessageSquare } from 'lucide-react';
import { Button } from '../foundation/buttons/Button';

export interface ContactSupportPanelProps {
  onContactSupport?: () => void;
}

export const ContactSupportPanel: React.FC<ContactSupportPanelProps> = ({
  onContactSupport,
}) => {
  return (
    <div className="p-8 rounded-ds-2xl bg-gradient-to-r from-indigo-50/90 via-white to-purple-50/90 dark:from-indigo-950/60 dark:via-slate-900/90 dark:to-purple-950/60 border border-indigo-200 dark:border-indigo-500/30 text-slate-900 dark:text-white flex flex-col sm:flex-row items-center justify-between gap-6 text-left shadow-ds-hero max-w-4xl mx-auto">
      <div className="space-y-1">
        <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold text-xs uppercase tracking-wider">
          <HelpCircle className="w-4 h-4" />
          <span>Still Have Questions?</span>
        </div>
        <h4 className="font-display font-extrabold text-xl text-slate-900 dark:text-white">
          Our Team is Happy to Help.
        </h4>
        <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
          Get in touch with our solutions engineers or schedule a live personalized walkthrough.
        </p>
      </div>


      <div className="flex items-center gap-3 shrink-0">
        <Button
          variant="primary"
          size="md"
          rightIcon={<ArrowRight className="w-4 h-4" />}
          onClick={onContactSupport}
        >
          Contact Support
        </Button>
      </div>
    </div>
  );
};
