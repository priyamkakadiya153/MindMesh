import React from 'react';
import { Building, ShieldCheck, ArrowRight, Server, Users } from 'lucide-react';
import { Button } from '../foundation/buttons/Button';

export interface EnterpriseContactPanelProps {
  onContactSales?: () => void;
}

export const EnterpriseContactPanel: React.FC<EnterpriseContactPanelProps> = ({
  onContactSales,
}) => {
  return (
    <div className="p-8 rounded-ds-2xl bg-gradient-to-r from-indigo-50/90 via-white to-purple-50/90 dark:from-indigo-950/60 dark:via-slate-900/90 dark:to-purple-950/60 border border-indigo-200 dark:border-indigo-500/30 text-slate-900 dark:text-white flex flex-col md:flex-row items-center justify-between gap-6 text-left shadow-ds-hero">
      <div className="space-y-2 max-w-2xl">
        <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold text-xs uppercase tracking-wider">
          <Building className="w-4 h-4" />
          <span>Need Custom Enterprise Deployment?</span>
        </div>
        <h4 className="font-display font-extrabold text-xl sm:text-2xl text-slate-900 dark:text-white">
          Dedicated Infrastructure & Volume Licensing.
        </h4>
        <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
          Custom AI model fine-tuning, isolated VPC deployment, custom data retention policies, and dedicated 24/7 solutions engineering support.
        </p>
      </div>


      <Button
        variant="primary"
        size="md"
        rightIcon={<ArrowRight className="w-4 h-4" />}
        onClick={onContactSales}
        className="shrink-0"
      >
        Talk to Enterprise Sales
      </Button>
    </div>
  );
};
