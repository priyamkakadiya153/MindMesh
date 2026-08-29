import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Sparkles,
  ArrowUp,
  Github,
  Linkedin,
  Twitter,
  Mail,
  BookOpen,
  ChevronDown,
  Sun,
  Moon,
  Laptop,
} from 'lucide-react';
import { PageContainer } from '../layout/Container';
import { IconButton } from '../buttons/IconButton';
import { useTheme } from '../../../../design-system/theme/useTheme';

export interface LandingFooterProps {
  onSignInClick?: () => void;
  onGetStartedClick?: () => void;
}

export const LandingFooter: React.FC<LandingFooterProps> = ({
  onSignInClick,
  onGetStartedClick,
}) => {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [openAccordion, setOpenAccordion] = useState<string | null>(null);

  // Monitor scroll for Back to Top floating button
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 400) {
        setShowBackToTop(true);
      } else {
        setShowBackToTop(false);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToTop = () => {
    const heroEl = document.getElementById('hero') || document.getElementById('main-content');
    if (heroEl) {
      heroEl.scrollIntoView({ behavior: 'smooth' });
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const handleSmoothScroll = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (href.startsWith('#')) {
      e.preventDefault();
      const targetId = href.substring(1);
      const targetElement = document.getElementById(targetId);
      if (targetElement) {
        targetElement.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  };


  const toggleAccordion = (colKey: string) => {
    setOpenAccordion(openAccordion === colKey ? null : colKey);
  };

  return (
    <footer className="relative bg-slate-50 dark:bg-slate-950 text-slate-700 dark:text-slate-300 border-t border-slate-200 dark:border-slate-800 pt-16 pb-12 overflow-hidden">
      {/* Background Subtle Grid Texture */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#e2e8f0_1px,transparent_1px),linear-gradient(to_bottom,#e2e8f0_1px,transparent_1px)] dark:bg-[linear-gradient(to_right,#1e293b_1px,transparent_1px),linear-gradient(to_bottom,#1e293b_1px,transparent_1px)] bg-[size:3rem_3rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-30 dark:opacity-20 pointer-events-none" />

      <PageContainer maxWidth="2xl" className="relative z-10 space-y-12">
        {/* 5-Column SaaS Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 lg:gap-10 text-left">
          {/* Column 1: Brand & Pitch */}
          <div className="lg:col-span-1 space-y-4">
            <a href="#hero" onClick={(e) => handleSmoothScroll(e, '#hero')} className="flex items-center gap-2.5 group">
              <div className="flex items-center justify-center w-8 h-8 rounded-ds-lg bg-indigo-600 text-white shadow-ds-soft group-hover:scale-105 transition-transform duration-200">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="font-display font-extrabold text-lg text-slate-900 dark:text-white tracking-tight">
                Mind<span className="text-indigo-600 dark:text-indigo-400">Mesh</span>
              </span>
            </a>

            <p className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold uppercase tracking-wider">
              Cognitive OS for Organizational Memory.
            </p>

            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed font-medium">
              Transform conversations, documents, decisions, and projects into searchable organizational intelligence.
            </p>

            <div className="flex items-center gap-2 pt-1">
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer"
                className="p-2 rounded-ds-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
                aria-label="GitHub Repository"
              >
                <Github className="w-4 h-4" />
              </a>
              <a
                href="#faq"
                onClick={(e) => handleSmoothScroll(e, '#faq')}
                className="p-2 rounded-ds-md bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
                aria-label="Documentation"
              >
                <BookOpen className="w-4 h-4" />
              </a>
              <span className="text-[10px] px-2 py-1 rounded-ds-full bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-500/20 font-mono font-medium">
                Roadmap Soon
              </span>
            </div>
          </div>

          {/* Column 2: Product */}
          <div className="space-y-3">
            <button
              onClick={() => toggleAccordion('product')}
              className="w-full flex items-center justify-between md:cursor-default font-display font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-white"
            >
              <span>Product</span>
              <ChevronDown className={`w-4 h-4 md:hidden transition-transform ${openAccordion === 'product' ? 'rotate-180' : ''}`} />
            </button>
            <ul className={`space-y-2 text-xs text-slate-600 dark:text-slate-400 font-medium ${openAccordion === 'product' ? 'block' : 'hidden md:block'}`}>
              <li><a href="#features" onClick={(e) => handleSmoothScroll(e, '#features')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Features</a></li>
              <li><a href="#intelligence" onClick={(e) => handleSmoothScroll(e, '#intelligence')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Intelligence</a></li>
              <li><a href="#how-it-works" onClick={(e) => handleSmoothScroll(e, '#how-it-works')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">How It Works</a></li>
              <li><a href="#pricing" onClick={(e) => handleSmoothScroll(e, '#pricing')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Pricing</a></li>
              <li><a href="#faq" onClick={(e) => handleSmoothScroll(e, '#faq')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">FAQ</a></li>
              <li><button onClick={onSignInClick} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors text-left">Sign In</button></li>
              <li><button onClick={onGetStartedClick} className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-semibold">Create Account</button></li>
            </ul>
          </div>

          {/* Column 3: Resources */}
          <div className="space-y-3">
            <button
              onClick={() => toggleAccordion('resources')}
              className="w-full flex items-center justify-between md:cursor-default font-display font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-white"
            >
              <span>Resources</span>
              <ChevronDown className={`w-4 h-4 md:hidden transition-transform ${openAccordion === 'resources' ? 'rotate-180' : ''}`} />
            </button>
            <ul className={`space-y-2 text-xs text-slate-600 dark:text-slate-400 font-medium ${openAccordion === 'resources' ? 'block' : 'hidden md:block'}`}>
              <li><a href="#faq" onClick={(e) => handleSmoothScroll(e, '#faq')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Documentation</a></li>
              <li><a href="#faq" onClick={(e) => handleSmoothScroll(e, '#faq')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">API Reference</a></li>
              <li><a href="#faq" onClick={(e) => handleSmoothScroll(e, '#faq')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Release Notes</a></li>
              <li><span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400 font-semibold"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />System Status: 100%</span></li>
              <li><span className="text-slate-500 flex items-center gap-1">Blog <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-mono font-medium">Soon</span></span></li>
            </ul>
          </div>

          {/* Column 4: Company */}
          <div className="space-y-3">
            <button
              onClick={() => toggleAccordion('company')}
              className="w-full flex items-center justify-between md:cursor-default font-display font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-white"
            >
              <span>Company</span>
              <ChevronDown className={`w-4 h-4 md:hidden transition-transform ${openAccordion === 'company' ? 'rotate-180' : ''}`} />
            </button>
            <ul className={`space-y-2 text-xs text-slate-600 dark:text-slate-400 font-medium ${openAccordion === 'company' ? 'block' : 'hidden md:block'}`}>
              <li><a href="#hero" onClick={(e) => handleSmoothScroll(e, '#hero')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">About MindMesh</a></li>
              <li><a href="#faq" onClick={(e) => handleSmoothScroll(e, '#faq')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Privacy Policy</a></li>
              <li><a href="#faq" onClick={(e) => handleSmoothScroll(e, '#faq')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Terms of Service</a></li>
              <li><a href="#faq" onClick={(e) => handleSmoothScroll(e, '#faq')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">Contact Sales</a></li>
              <li><span className="text-slate-500 flex items-center gap-1">Careers <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-mono font-medium">Hiring</span></span></li>
            </ul>
          </div>

          {/* Column 5: Social Connections */}
          <div className="space-y-3">
            <h4 className="font-display font-bold text-xs uppercase tracking-wider text-slate-900 dark:text-white">Social</h4>
            <div className="flex flex-col space-y-2.5 text-xs text-slate-600 dark:text-slate-400 font-medium">
              <a href="https://linkedin.com" target="_blank" rel="noreferrer" className="flex items-center gap-2 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                <Linkedin className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                <span>LinkedIn</span>
              </a>
              <a href="https://github.com" target="_blank" rel="noreferrer" className="flex items-center gap-2 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                <Github className="w-4 h-4 text-slate-700 dark:text-slate-300" />
                <span>GitHub</span>
              </a>
              <a href="https://twitter.com" target="_blank" rel="noreferrer" className="flex items-center gap-2 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                <Twitter className="w-4 h-4 text-sky-500" />
                <span>Twitter/X</span>
              </a>
              <a href="mailto:hello@mindmesh.ai" className="flex items-center gap-2 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                <Mail className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                <span>hello@mindmesh.ai</span>
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Bar Divider */}
        <div className="pt-8 border-t border-slate-200 dark:border-slate-800/80 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-500 font-medium">
          <div>
            © 2026 MindMesh. Built with ❤️ for teams that never want to lose knowledge again.
          </div>

          <div className="flex items-center gap-4">
            <span className="px-2 py-0.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 font-mono text-[11px]">
              Version v1.0.0
            </span>

            <IconButton
              icon={resolvedTheme === 'dark' ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-indigo-600" />}
              aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            />

            <button
              onClick={scrollToTop}
              className="flex items-center gap-1 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white font-semibold transition-colors focus-ring rounded p-1"
            >
              <span>Back to top</span>
              <ArrowUp className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </PageContainer>


      {/* Floating Back To Top Button */}
      <AnimatePresence>
        {showBackToTop && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 10 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            onClick={scrollToTop}
            aria-label="Back to top"
            className="fixed bottom-6 right-6 z-40 p-3 rounded-full bg-indigo-600 text-white shadow-ds-hero hover:bg-indigo-500 transition-all duration-200 hover:scale-110 focus-ring"
          >
            <ArrowUp className="w-5 h-5" />
          </motion.button>
        )}
      </AnimatePresence>
    </footer>
  );
};
