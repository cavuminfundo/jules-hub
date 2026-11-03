import React from 'react';
import { X, Play, Loader2, Sparkles } from 'lucide-react';
import type { Suggestion } from '../types';

interface SuggestionCardProps {
  suggestion: Suggestion;
  onRunInJulius: (suggestion: Suggestion) => void;
  onEscalateToAntigravity?: (suggestion: Suggestion) => void;
  onDiscard?: (id: string) => void;
  isRunning?: boolean;
  isEscalating?: boolean;
}

export const SuggestionCard: React.FC<SuggestionCardProps> = ({
  suggestion,
  onRunInJulius,
  onDiscard,
  isRunning = false,
}) => {
  // Map category to Julius official labels & codes
  const getCategoryDetails = (cat: string) => {
    const c = cat.toLowerCase();
    switch (c) {
      case 'cleanup':
      case 'hygiene':
        return { code: 'ch', label: 'healing' };
      case 'performance':
        return { code: 'pa', label: 'speed' };
      case 'security':
        return { code: 'sh', label: 'security' };
      case 'testing':
      case 'tests':
        return { code: 'bc', label: 'science' };
      case 'code_health':
        return { code: 'ch', label: 'code health' };
      default:
        return { code: 'pa', label: c || 'healing' };
    }
  };

  const { code, label } = getCategoryDetails(suggestion.category);

  const getPersonaInitial = (persona: string) => {
    const p = persona.toLowerCase();
    if (p === 'bolt') return 'B';
    if (p === 'palette') return 'P';
    if (p === 'sentinel') return 'S';
    return persona.charAt(0).toUpperCase();
  };

  return (
    <article className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-zinc-800/50 transition-colors gap-3 group">
      {/* Left side: Category code, title, and badge */}
      <div className="flex items-center gap-3 min-w-0 flex-1">
        {/* Category code icon */}
        <span
          className="font-mono text-xs font-semibold text-zinc-400 bg-zinc-800/80 px-1.5 py-0.5 rounded shrink-0"
          title={`Category code: ${code}`}
        >
          {code}
        </span>

        {/* Suggestion title and file context */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <h4 className="text-sm text-zinc-100 font-medium truncate">
              {suggestion.title}
            </h4>
            <span className="bg-zinc-800/90 text-zinc-300 text-[11px] px-2 py-0.5 rounded-md shrink-0 font-normal">
              {label}
            </span>
          </div>
          <p className="text-[11px] text-zinc-400 truncate mt-0.5">
            {suggestion.file}:{suggestion.line} • {suggestion.issue}
          </p>
        </div>
      </div>

      {/* Right side: Confidence bars, Start button, Persona avatar, Discard X */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* Confidence 3 vertical bars */}
        <div
          className="hidden sm:flex items-end gap-[2px] h-3.5 px-1 py-0.5"
          title="Confidence: High"
          aria-label="High confidence indicator"
        >
          <span className="w-1 h-2 bg-emerald-500 rounded-xs" />
          <span className="w-1 h-3 bg-emerald-500 rounded-xs" />
          <span className="w-1 h-3.5 bg-emerald-500 rounded-xs" />
        </div>

        {/* Start button */}
        <button
          type="button"
          onClick={() => onRunInJulius(suggestion)}
          disabled={isRunning}
          title="Start task in worktree"
          aria-label={`Start task: ${suggestion.title}`}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 min-h-[36px] rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-100 text-xs font-medium transition-colors disabled:opacity-50"
        >
          {isRunning ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Starting...</span>
            </>
          ) : (
            <>
              <Play className="w-3 h-3 fill-current text-zinc-300" />
              <span>Start</span>
            </>
          )}
        </button>

        {/* Persona avatar badge (violet circle) */}
        <span
          className="w-6 h-6 rounded-full bg-[#6d28d9] text-white text-[11px] flex items-center justify-center font-semibold shrink-0 select-none shadow-xs"
          title={`Persona: ${suggestion.persona}`}
        >
          {getPersonaInitial(suggestion.persona)}
        </span>

        {/* Discard button */}
        {onDiscard && (
          <button
            type="button"
            onClick={() => onDiscard(suggestion.id)}
            aria-label="Discard suggestion"
            title="Discard suggestion"
            className="p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-md text-zinc-400 hover:text-rose-400 hover:bg-zinc-800/80 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </article>
  );
};

export const SuggestionSkeleton: React.FC = () => {
  return (
    <div className="flex items-center justify-between py-3 px-3 rounded-lg animate-pulse gap-3">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <div className="h-5 w-6 bg-zinc-800 rounded shrink-0" />
        <div className="space-y-1.5 flex-1 min-w-0">
          <div className="h-4 w-1/2 bg-zinc-800 rounded" />
          <div className="h-3 w-1/3 bg-zinc-800/70 rounded" />
        </div>
      </div>
      <div className="flex items-center gap-2 shrink-0">
        <div className="h-7 w-16 bg-zinc-800 rounded" />
        <div className="h-6 w-6 rounded-full bg-zinc-800" />
      </div>
    </div>
  );
};

export const SuggestionEmptyState: React.FC<{
  repoName?: string;
  onRefresh?: () => void;
}> = ({ repoName, onRefresh }) => {
  return (
    <div className="py-12 px-4 text-center flex flex-col items-center justify-center rounded-xl bg-zinc-900/30 border border-dashed border-zinc-800/80">
      <div className="w-10 h-10 rounded-full bg-zinc-800/80 flex items-center justify-center text-zinc-400 mb-3">
        <Sparkles className="w-5 h-5 text-zinc-400" />
      </div>
      <h4 className="text-sm font-semibold text-zinc-200 mb-1">
        No pending suggestions
      </h4>
      <p className="text-xs text-zinc-400 max-w-sm mb-4">
        {repoName
          ? `Repository "${repoName}" has no suggestions found for this category.`
          : 'All clear — No pending suggestions found.'}
      </p>
      {onRefresh && (
        <button
          type="button"
          onClick={onRefresh}
          className="px-3 py-1.5 min-h-[36px] rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium transition-colors"
        >
          Refresh scan
        </button>
      )}
    </div>
  );
};
