import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export interface CountryCodeOption {
  code: string;
  country: string;
  flag: string;
  minLength: number;
  maxLength: number;
}

export const COUNTRY_CODES: CountryCodeOption[] = [
  { code: '+91', country: 'India', flag: '🇮🇳', minLength: 10, maxLength: 10 },
  { code: '+1', country: 'US / Canada', flag: '🇺🇸', minLength: 10, maxLength: 10 },
  { code: '+44', country: 'United Kingdom', flag: '🇬🇧', minLength: 10, maxLength: 10 },
  { code: '+971', country: 'UAE', flag: '🇦🇪', minLength: 9, maxLength: 9 },
  { code: '+61', country: 'Australia', flag: '🇦🇺', minLength: 9, maxLength: 9 },
  { code: '+49', country: 'Germany', flag: '🇩🇪', minLength: 10, maxLength: 11 },
  { code: '+33', country: 'France', flag: '🇫🇷', minLength: 9, maxLength: 9 },
  { code: '+65', country: 'Singapore', flag: '🇸🇬', minLength: 8, maxLength: 8 },
  { code: '+81', country: 'Japan', flag: '🇯🇵', minLength: 10, maxLength: 10 },
];

export const getCountryRule = (code: string): CountryCodeOption => {
  return (
    COUNTRY_CODES.find((c) => c.code === code) || {
      code,
      country: 'Unknown',
      flag: '🌐',
      minLength: 7,
      maxLength: 15,
    }
  );
};

interface CountrySelectorProps {
  value: string;
  onChange: (code: string) => void;
  disabled?: boolean;
}

export const CountrySelector: React.FC<CountrySelectorProps> = ({ value, onChange, disabled }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const selectedCountry = getCountryRule(value);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
    if (!isOpen) {
      setSearchQuery('');
    }
  }, [isOpen]);

  const filteredCountries = COUNTRY_CODES.filter(
    (c) =>
      c.country.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.code.includes(searchQuery)
  );

  const handleSelect = (code: string) => {
    onChange(code);
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      setIsOpen((prev) => !prev);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  };

  return (
    <div ref={containerRef} className="relative shrink-0 select-none">
      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen((prev) => !prev)}
        onKeyDown={handleKeyDown}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Select Country Code"
        className="flex items-center justify-between gap-1.5 w-[96px] h-full bg-bgInput border border-borderColor rounded-l-lg px-2.5 py-2.5 text-sm font-semibold text-textPrimary outline-none transition-all cursor-pointer hover:border-accent hover:bg-bgTertiary/50 focus-visible:ring-2 focus-visible:ring-accent disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span className="flex items-center gap-1.5 truncate">
          <span className="text-base leading-none">{selectedCountry.flag}</span>
          <span className="text-sm font-semibold text-textPrimary tracking-tight">{selectedCountry.code}</span>
        </span>
        <ChevronDown
          className={`w-3.5 h-3.5 text-textMuted shrink-0 transition-transform duration-200 ${
            isOpen ? 'rotate-180 text-accent' : ''
          }`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            role="listbox"
            className="absolute left-0 top-full mt-1.5 z-50 w-60 bg-bgInput border border-borderColor rounded-xl shadow-2xl backdrop-blur-xl p-1.5 space-y-1 overflow-hidden"
          >
            {/* Search Input */}
            <div className="relative px-2 pt-1 pb-1.5 border-b border-borderColor/60">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-textMuted" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search country or code..."
                className="w-full bg-bgTertiary border border-borderColor/60 rounded-md pl-7 pr-2 py-1 text-xs text-textPrimary placeholder:text-textMuted outline-none focus:border-accent"
              />
            </div>

            <div className="max-h-52 overflow-y-auto space-y-0.5 custom-scrollbar">
              {filteredCountries.length === 0 ? (
                <div className="px-3 py-2 text-xs text-textMuted text-center">No countries found</div>
              ) : (
                filteredCountries.map((c) => {
                  const isSelected = c.code === value;
                  return (
                    <button
                      key={c.code}
                      type="button"
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => handleSelect(c.code)}
                      className={`flex items-center justify-between w-full px-3 py-2 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                        isSelected
                          ? 'bg-accent/15 text-accent font-semibold'
                          : 'text-textPrimary hover:bg-bgTertiary hover:text-textPrimary'
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        <span className="text-base leading-none">{c.flag}</span>
                        <span className="font-semibold text-textPrimary">{c.code}</span>
                        <span className="text-textMuted">({c.country})</span>
                      </span>
                      {isSelected && <Check className="w-3.5 h-3.5 text-accent shrink-0" />}
                    </button>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
