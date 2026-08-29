import React, { useState, useRef, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface SidebarCollapseProps {
  collapsed: boolean;
  onToggle: () => void;
  isMobile?: boolean;
}

export function SidebarCollapse({ collapsed, onToggle, isMobile = false }: SidebarCollapseProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const handleMouseEnter = () => {
    if (isMobile) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setShowTooltip(true);
    }, 300);
  };

  const handleMouseLeave = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setShowTooltip(false);
  };

  const handleFocus = () => {
    if (isMobile) return;
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setShowTooltip(true);
    }, 300);
  };

  const handleBlur = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setShowTooltip(false);
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const ariaText = collapsed ? "Open sidebar" : "Collapse sidebar";

  return (
    <div className="relative inline-flex items-center">
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          onToggle();
        }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onFocus={handleFocus}
        onBlur={handleBlur}
        aria-label={ariaText}
        aria-expanded={!collapsed}
        title={ariaText}
        className={`
          h-8 w-8 sm:h-9 sm:w-9 rounded-full
          bg-bgCard hover:bg-bgHover border border-borderColor
          text-textPrimary hover:text-accentText
          shadow-sm hover:shadow-md hover:scale-105 active:scale-95
          focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent
          transition-all duration-200 ease-out
          flex items-center justify-center shrink-0 cursor-pointer
          opacity-70 hover:opacity-100 focus-visible:opacity-100
        `}
      >
        {collapsed ? (
          <ChevronRight size={18} className="transition-transform duration-200" aria-hidden="true" />
        ) : (
          <ChevronLeft size={18} className="transition-transform duration-200" aria-hidden="true" />
        )}
      </button>

      {/* Floating Tooltip */}
      {showTooltip && (
        <div
          role="tooltip"
          className={`
            absolute z-50 whitespace-nowrap rounded-lg px-2.5 py-1.5 text-xs font-semibold
            bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900
            shadow-xl border border-slate-800 dark:border-slate-200
            pointer-events-none transition-all duration-200 ease-out
            ${collapsed
              ? 'left-full ml-3 top-1/2 -translate-y-1/2'
              : 'right-0 top-full mt-2 sm:right-auto sm:left-full sm:ml-3 sm:top-1/2 sm:-translate-y-1/2'
            }
          `}
        >
          {ariaText}
        </div>
      )}
    </div>
  );
}

export default SidebarCollapse;
