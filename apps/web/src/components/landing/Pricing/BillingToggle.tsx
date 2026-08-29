import React from 'react';
import { motion } from 'framer-motion';
import { Badge } from '../foundation/feedback/Badge';

export interface BillingToggleProps {
  isYearly: boolean;
  onToggle: (yearly: boolean) => void;
}

export const BillingToggle: React.FC<BillingToggleProps> = ({
  isYearly,
  onToggle,
}) => {
  return (
    <div className="flex items-center justify-center gap-3">
      <span className={`text-xs font-semibold ${!isYearly ? 'text-white' : 'text-slate-400'}`}>
        Monthly Billing
      </span>

      <button
        type="button"
        role="switch"
        aria-checked={isYearly}
        onClick={() => onToggle(!isYearly)}
        className="relative w-14 h-7 rounded-full bg-slate-900 border border-slate-800 p-1 flex items-center cursor-pointer focus-ring"
      >
        <motion.div
          animate={{ x: isYearly ? 26 : 0 }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          className="w-5 h-5 rounded-full bg-indigo-500 shadow-ds-soft"
        />
      </button>

      <div className="flex items-center gap-2">
        <span className={`text-xs font-semibold ${isYearly ? 'text-white' : 'text-slate-400'}`}>
          Annual Billing
        </span>
        <Badge variant="success" className="text-[10px] font-mono">
          Save 20%
        </Badge>
      </div>
    </div>
  );
};
