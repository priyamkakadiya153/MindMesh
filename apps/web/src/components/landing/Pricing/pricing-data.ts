export interface PricingTier {
  id: 'free' | 'pro' | 'enterprise';
  name: string;
  badge?: string;
  monthlyPrice: number | string;
  yearlyPrice: number | string;
  period: string;
  description: string;
  isRecommended?: boolean;
  ctaText: string;
  ctaVariant: 'primary' | 'secondary' | 'outline';
  features: string[];
}

export interface PricingFAQ {
  question: string;
  answer: string;
}

export const PRICING_TIERS: PricingTier[] = [
  {
    id: 'free',
    name: 'Free',
    monthlyPrice: 0,
    yearlyPrice: 0,
    period: 'forever',
    description: 'Perfect for individual developers and small personal knowledge spaces.',
    ctaText: 'Get Started Free — No Credit Card',
    ctaVariant: 'outline',

    features: [
      'Up to 5 Workspaces',
      '50 Knowledge Documents',
      '0.04s Semantic Vector Search',
      'Context-Aware AI Chat Assistant',
      'Basic Metadata Extraction',
      'Community Support',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    badge: 'Most Popular ⭐',
    monthlyPrice: 19,
    yearlyPrice: 15,
    period: 'per user / month',
    description: 'Designed for high-velocity engineering & product teams needing living memory.',
    isRecommended: true,
    ctaText: 'Start 14-Day Free Trial',
    ctaVariant: 'primary',
    features: [
      'Up to 25 Workspaces',
      'Unlimited Knowledge Documents',
      'Full Living Knowledge Graph',
      '100% Grounded RAG with Citations',
      'Automatic Decision Extraction',
      'Multi-Format Ingestion (PDF, MD, Code)',
      'Priority 24/7 Support',
    ],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    monthlyPrice: 'Custom',
    yearlyPrice: 'Custom',
    period: 'tailored licensing',
    description: 'Built for organizations requiring SOC2 compliance, custom AI, & dedicated SLA.',
    ctaText: 'Contact Sales',
    ctaVariant: 'secondary',
    features: [
      'Unlimited Enterprise Workspaces',
      'Multi-Tenant Data Isolation',
      'SAML SSO (Google & Entra ID)',
      'Immutable Enterprise Audit Logs',
      'Custom AI Model Integrations',
      '99.9% Uptime SLA Guarantee',
      'Dedicated Success Manager',
    ],
  },
];

export const PRICING_FAQS: PricingFAQ[] = [
  {
    question: 'Can I upgrade or downgrade my plan at any time?',
    answer:
      'Yes! You can upgrade from Free to Pro or Enterprise instantly. Downgrades take effect at the end of your current billing cycle with zero data loss.',
  },
  {
    question: 'Do you offer annual billing discounts?',
    answer:
      'Yes, paying annually saves 20% compared to monthly billing across all Pro workspace seats.',
  },
  {
    question: 'Is there a free trial for the Pro plan?',
    answer:
      'Yes, all new teams receive a 14-day full access free trial of the Pro plan with no credit card required upfront.',
  },
  {
    question: 'How is enterprise workspace data protected?',
    answer:
      'MindMesh enforces AES-256 data encryption at rest, TLS 1.3 in transit, strict RBAC tenant isolation, and SOC2 Type II security controls.',
  },
  {
    question: 'Can I invite team members across multiple workspaces?',
    answer:
      'Absolutely! Workspace Owners and Admins can manage member roles, invite teammates, and share document citations seamlessly.',
  },
];
