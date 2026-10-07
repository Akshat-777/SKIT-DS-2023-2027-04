import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Search, Check, Briefcase, Sparkles, X } from 'lucide-react';

export const CURATED_ROLES = [
  'Data Scientist / ML Engineer',
  'AI / NLP Research Engineer',
  'MLOps & Cloud Infrastructure Engineer',
  'Full Stack AI Application Developer',
  'Data Analyst / Business Intelligence',
  'Computer Vision & OCR Engineer',
  'Python Backend Engineer (FastAPI)',
  'Generative AI & LLM Systems Engineer',
  'Big Data & Data Pipeline Engineer',
  'Software Development Engineer (SDE-1)',
];

/**
 * CareerLens TargetRoleSelector
 * Searchable dropdown with keyboard navigation, custom role typing, and clean accessibility.
 */
export default function TargetRoleSelector({
  value = '',
  onChange,
  disabled = false,
  className = '',
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(0);

  const containerRef = useRef(null);
  const searchInputRef = useRef(null);

  // Filter roles based on search
  const filteredRoles = CURATED_ROLES.filter((role) =>
    role.toLowerCase().includes(searchQuery.toLowerCase().trim())
  );

  const isCustomInput =
    searchQuery.trim().length > 0 &&
    !CURATED_ROLES.some((r) => r.toLowerCase() === searchQuery.toLowerCase().trim());

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        if (searchInputRef.current) {
          searchInputRef.current.focus();
        }
      }, 50);
      setHighlightedIndex(0);
    } else {
      setSearchQuery('');
    }
  }, [isOpen]);

  const selectRole = (role) => {
    onChange(role);
    setIsOpen(false);
  };

  const handleKeyDown = (e) => {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
        e.preventDefault();
        setIsOpen(true);
      }
      return;
    }

    const totalItems = filteredRoles.length + (isCustomInput ? 1 : 0);

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev + 1) % Math.max(1, totalItems));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setHighlightedIndex((prev) => (prev - 1 + totalItems) % Math.max(1, totalItems));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (isCustomInput && highlightedIndex === filteredRoles.length) {
        selectRole(searchQuery.trim());
      } else if (filteredRoles[highlightedIndex]) {
        selectRole(filteredRoles[highlightedIndex]);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      setIsOpen(false);
    }
  };

  return (
    <div ref={containerRef} className={`relative w-full ${className}`}>
      <label
        htmlFor="target-role-button"
        className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5 uppercase tracking-wider"
      >
        Target Role for Live Market Benchmarking <span className="text-rose-500">*</span>
      </label>

      {/* Main Trigger Button */}
      <button
        id="target-role-button"
        type="button"
        data-testid="target-role-trigger"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        disabled={disabled}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        className={`w-full flex items-center justify-between px-4 py-2.5 bg-white dark:bg-slate-850 rounded-xl border text-left transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-brand-500 shadow-xs ${
          isOpen
            ? 'border-brand-500 ring-2 ring-brand-500/20'
            : 'border-slate-300 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-600'
        } ${disabled ? 'opacity-60 cursor-not-allowed bg-slate-50 dark:bg-slate-900' : 'cursor-pointer'}`}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-7 h-7 rounded-lg bg-brand-50 dark:bg-brand-950/70 text-brand-600 dark:text-brand-400 flex items-center justify-center flex-shrink-0">
            <Briefcase className="w-4 h-4" />
          </div>
          <span
            className={`text-sm font-semibold truncate ${
              value ? 'text-slate-900 dark:text-slate-100' : 'text-slate-400'
            }`}
          >
            {value || 'Select target job role for ATS scoring...'}
          </span>
        </div>

        <ChevronDown
          className={`w-4 h-4 text-slate-400 transition-transform duration-200 flex-shrink-0 ml-2 ${
            isOpen ? 'rotate-180 text-brand-500' : ''
          }`}
        />
      </button>

      <p className="mt-1 text-2xs text-slate-500 dark:text-slate-400">
        CareerLens will fetch real-time market skills demand and recruiter criteria for this role.
      </p>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          role="listbox"
          data-testid="target-role-listbox"
          className="absolute z-40 left-0 right-0 mt-2 bg-white dark:bg-slate-850 rounded-xl border border-slate-200 dark:border-slate-700 shadow-xl overflow-hidden animate-fade-in"
        >
          {/* Search Box */}
          <div className="p-2 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 flex items-center gap-2">
            <Search className="w-4 h-4 text-slate-400 ml-1.5 flex-shrink-0" />
            <input
              ref={searchInputRef}
              type="text"
              data-testid="target-role-search-input"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setHighlightedIndex(0);
              }}
              onKeyDown={handleKeyDown}
              placeholder="Search or type custom job role..."
              className="w-full bg-transparent text-xs text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none py-1"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery('')}
                className="p-1 text-slate-400 hover:text-slate-600 rounded"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* List of Roles */}
          <div className="max-h-60 overflow-y-auto py-1 divide-y divide-slate-50 dark:divide-slate-800/40">
            {filteredRoles.map((role, idx) => {
              const isSelected = value === role;
              const isHighlighted = idx === highlightedIndex;

              return (
                <div
                  key={role}
                  role="option"
                  aria-selected={isSelected}
                  data-testid={`role-option-${idx}`}
                  onClick={() => selectRole(role)}
                  onMouseEnter={() => setHighlightedIndex(idx)}
                  className={`flex items-center justify-between px-3.5 py-2.5 text-xs font-medium cursor-pointer transition-colors ${
                    isHighlighted
                      ? 'bg-brand-50 dark:bg-brand-950/50 text-brand-700 dark:text-brand-300'
                      : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <span className="truncate">{role}</span>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-brand-600 dark:text-brand-400 flex-shrink-0" />}
                </div>
              );
            })}

            {/* Custom typed role item */}
            {isCustomInput && (
              <div
                role="option"
                data-testid="custom-role-option"
                aria-selected={value === searchQuery.trim()}
                onClick={() => selectRole(searchQuery.trim())}
                onMouseEnter={() => setHighlightedIndex(filteredRoles.length)}
                className={`flex items-center justify-between px-3.5 py-2.5 text-xs font-semibold cursor-pointer border-t border-brand-100 dark:border-brand-950/60 ${
                  highlightedIndex === filteredRoles.length
                    ? 'bg-brand-100/70 dark:bg-brand-900/60 text-brand-800 dark:text-brand-200'
                    : 'bg-brand-50/50 dark:bg-brand-950/30 text-brand-700 dark:text-brand-300'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <Sparkles className="w-3.5 h-3.5 text-brand-500 flex-shrink-0" />
                  <span className="truncate">Use custom: &quot;{searchQuery.trim()}&quot;</span>
                </div>
                <span className="text-3xs px-1.5 py-0.5 rounded bg-brand-200 dark:bg-brand-800 font-mono">
                  Custom
                </span>
              </div>
            )}

            {filteredRoles.length === 0 && !isCustomInput && (
              <div className="px-4 py-6 text-center text-xs text-slate-400">
                No matching roles found. Type to enter a custom role.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
