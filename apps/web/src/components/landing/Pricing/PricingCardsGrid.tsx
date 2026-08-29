import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Sparkles, ArrowRight } from 'lucide-react';
import { PRICING_TIERS, PricingTier } from './pricing-data';
import { Badge } from '../foundation/feedback/Badge';
import { Button } from '../foundation/buttons/Button';

export interface PricingCardsGridProps {
  isYearly: boolean;
  onSelectPlan: (tier: PricingTier) => void;
}

export const PricingCardsGrid: React.FC<PricingCardsGridProps> = ({
  isYearly,
  onSelectPlan,
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch text-left">
      {PRICING_TIERS.map((tier) => {
        const isRec = tier.isRecommended;
        const priceDisplay =
          typeof tier.monthlyPrice === 'number'
            ? isYearly
              ? `$${tier.yearlyPrice}`
              : `$${tier.monthlyPrice}`
            : tier.monthlyPrice;

        return (
          <motion.div
            key={tier.id}
            whileHover={{ y: -4, scale: 1.01 }}
            transition={{ type: 'spring', stiffness: 450, damping: 25 }}
            className={`
              p-6 sm:p-8 rounded-ds-2xl border flex flex-col justify-between transition-colors duration-200 relative
              ${
                isRec
                  ? 'bg-gradient-to-b from-indigo-50/90 via-white to-slate-50 dark:from-indigo-950/80 dark:via-slate-900/95 dark:to-slate-900/95 border-indigo-500/50 shadow-ds-hero lg:-translate-y-2'
                  : 'bg-white dark:bg-slate-900/80 border-slate-200 dark:border-slate-800 shadow-ds-medium hover:border-indigo-400 dark:hover:border-slate-700'
              }
            `.trim()}
          >

            {/* Recommended Badge Header */}
            {isRec && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <Badge variant="primary" className="text-[10px] font-mono shadow-ds-soft">
                  {tier.badge}
                </Badge>
              </div>
            )}

            <div className="space-y-6">
              {/* Card Header */}
              <div className="space-y-2">
                <h3 className="font-display font-extrabold text-xl text-slate-900 dark:text-white">{tier.name}</h3>
                <p className="text-xs text-slate-600 dark:text-slate-400 min-h-[36px] font-medium">{tier.description}</p>
              </div>

              {/* Price Display */}
              <div className="flex items-baseline gap-2 pb-4 border-b border-slate-200 dark:border-slate-800">
                <span className="font-display font-extrabold text-4xl text-slate-900 dark:text-white tracking-tight">
                  {priceDisplay}
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">
                  {typeof tier.monthlyPrice === 'number' ? `/ ${tier.period}` : tier.period}
                </span>
              </div>

              {/* Feature Checklist */}
              <div className="space-y-2.5 text-xs">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 block">
                  Included Capabilities:
                </span>
                {tier.features.map((feat) => (
                  <div key={feat} className="flex items-center gap-2 text-slate-700 dark:text-slate-200">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400 shrink-0" />
                    <span>{feat}</span>
                  </div>
                ))}
              </div>
            </div>


            {/* CTA Button */}
            <div className="pt-6">
              <Button
                variant={tier.ctaVariant}
                size="md"
                rightIcon={<ArrowRight className="w-4 h-4" />}
                onClick={() => onSelectPlan(tier)}
                className="w-full min-h-[48px] font-bold"
              >
                {tier.ctaText}
              </Button>
            </div>

          </motion.div>
        );
      })}

    </div>
  );
};
