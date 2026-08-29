import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, Sun, Moon, Laptop, Sparkles, ArrowRight } from 'lucide-react';
import { Button } from '../buttons/Button';
import { IconButton } from '../buttons/IconButton';
import { NavigationLink } from './NavigationLink';
import { useTheme } from '../../../../design-system/theme/useTheme';

export interface NavItem {
  label: string;
  href: string;
}

export interface LandingNavbarProps {
  navItems?: NavItem[];
  activeSection?: string;
  onSignInClick?: () => void;
  onGetStartedClick?: () => void;
}

const DEFAULT_NAV_ITEMS: NavItem[] = [
  { label: 'Features', href: '#features' },
  { label: 'Intelligence', href: '#intelligence' },
  { label: 'How it Works', href: '#how-it-works' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'FAQ', href: '#faq' },
];

export const LandingNavbar: React.FC<LandingNavbarProps> = ({
  navItems = DEFAULT_NAV_ITEMS,
  activeSection = '',
  onSignInClick,
  onGetStartedClick,
}) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();

  const [currentActiveSection, setCurrentActiveSection] = useState(activeSection);

  // Handle scroll detection for sticky navbar opacity & backdrop blur
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setIsScrolled(true);
      } else {
        setIsScrolled(false);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Active section tracking via IntersectionObserver
  useEffect(() => {
    const sectionIds = navItems.map((item) => item.href.replace('#', '')).filter(Boolean);
    const observerCallback: IntersectionObserverCallback = (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          setCurrentActiveSection(entry.target.id);
        }
      });
    };

    const observerOptions: IntersectionObserverInit = {
      root: null,
      rootMargin: '-20% 0px -60% 0px',
      threshold: 0,
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);
    sectionIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [navItems]);

  // Prevent scroll when mobile menu is open
  useEffect(() => {
    if (isMobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isMobileMenuOpen]);


  const handleSmoothScroll = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (href.startsWith('#')) {
      e.preventDefault();
      const targetId = href.substring(1);
      const targetElement = document.getElementById(targetId);
      if (targetElement) {
        targetElement.scrollIntoView({ behavior: 'smooth' });
        setIsMobileMenuOpen(false);
      }
    }
  };

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <header
      className={`
        fixed top-0 left-0 right-0 z-40 transition-all duration-300
        ${
          isScrolled
            ? 'bg-white/80 dark:bg-slate-950/85 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800/80 shadow-ds-soft py-3'
            : 'bg-transparent py-5'
        }
      `.trim()}
    >
      <div className="max-w-7xl mx-auto px-4 mobile-sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Brand Logo */}
          <a
            href="#"
            className="flex items-center gap-2.5 group focus-ring rounded-ds-md py-1 px-1.5"
          >
            <div className="relative flex items-center justify-center w-9 h-9 rounded-ds-lg bg-indigo-600 text-white shadow-ds-soft group-hover:scale-105 transition-transform duration-200">
              <Sparkles className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-display font-extrabold text-lg tracking-tight text-slate-900 dark:text-white">
                Mind<span className="text-indigo-600 dark:text-indigo-400">Mesh</span>
              </span>
              <span className="text-[10px] uppercase font-bold tracking-widest text-slate-400 -mt-1">
                Knowledge AI
              </span>
            </div>
          </a>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-6" aria-label="Main Navigation">
            {navItems.map((item) => (
              <NavigationLink
                key={item.href}
                href={item.href}
                active={currentActiveSection === item.href.substring(1)}

                onClick={(e) => handleSmoothScroll(e, item.href)}
              >
                {item.label}
              </NavigationLink>
            ))}
          </nav>

          {/* Right Action Group */}
          <div className="hidden md:flex items-center gap-3">
            {/* Theme Switcher Button (Light / Dark) */}
            <IconButton
              icon={resolvedTheme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
              aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
              variant="ghost"
              size="md"
              onClick={toggleTheme}
            />


            <Button variant="ghost" size="sm" onClick={onSignInClick}>
              Sign In
            </Button>
            <Button
              variant="primary"
              size="sm"
              rightIcon={<ArrowRight className="w-4 h-4" />}
              onClick={onGetStartedClick}
              className="font-bold"
            >
              Start Free
            </Button>

          </div>

          {/* Mobile Navigation Controls */}
          <div className="flex items-center gap-2 md:hidden">
            <IconButton
              icon={resolvedTheme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
              aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
              variant="ghost"
              size="md"
              onClick={toggleTheme}
            />


            <IconButton
              icon={isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              aria-label={isMobileMenuOpen ? 'Close mobile menu' : 'Open mobile menu'}
              variant="ghost"
              size="md"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            />
          </div>
        </div>
      </div>

      {/* Mobile Animated Drawer Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="md:hidden overflow-hidden bg-white/95 dark:bg-slate-950/95 border-b border-slate-200 dark:border-slate-800 backdrop-blur-xl"
          >
            <div className="px-4 mobile-sm:px-6 pt-4 pb-[calc(1.5rem+env(safe-area-inset-bottom,0px))] space-y-4">
              <nav className="flex flex-col space-y-1">
                {navItems.map((item) => (
                  <a
                    key={item.href}
                    href={item.href}
                    onClick={(e) => handleSmoothScroll(e, item.href)}
                    className={`
                      px-4 py-3 rounded-ds-lg text-base font-semibold transition-colors min-h-[48px] flex items-center
                      ${
                        activeSection === item.href.substring(1)
                          ? 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-400 font-bold'
                          : 'text-slate-800 dark:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-900'
                      }
                    `.trim()}
                  >
                    {item.label}
                  </a>
                ))}
              </nav>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex flex-col gap-3">
                <button
                  type="button"
                  onClick={toggleTheme}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-ds-lg bg-slate-100 dark:bg-slate-900 text-slate-800 dark:text-slate-200 font-semibold text-sm min-h-[48px]"
                >
                  <span className="flex items-center gap-2">
                    {resolvedTheme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
                    <span>{resolvedTheme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}</span>
                  </span>
                  <span className="text-xs font-mono text-slate-400 uppercase">{resolvedTheme}</span>
                </button>

                <Button variant="outline" fullWidth onClick={onSignInClick} className="min-h-[48px] font-bold">
                  Sign In
                </Button>
                <Button
                  variant="primary"
                  fullWidth
                  rightIcon={<ArrowRight className="w-4 h-4" />}
                  onClick={onGetStartedClick}
                  className="min-h-[48px] font-bold"
                >
                  Get Started Free
                </Button>
              </div>
            </div>


          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};
