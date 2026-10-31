import React from 'react';
import {
  Zap,
  Palette,
  Shield,
  Play,
  Send,
  FileCode2,
  AlertCircle,
  Sparkles,
  Trash2,
} from 'lucide-react';
import type { Suggestion } from '../types';

interface SuggestionCardProps {
  suggestion: Suggestion;
  onRunInJules: (suggestion: Suggestion) => void;
  onEscalateToAntigravity: (suggestion: Suggestion) => void;
  onDiscard?: (id: string) => void;
  isRunning?: boolean;
  isEscalating?: boolean;
}

export const SuggestionCard: React.FC<SuggestionCardProps> = ({
  suggestion,
  onRunInJules,
  onEscalateToAntigravity,
  onDiscard,
  isRunning = false,
  isEscalating = false,
}) => {
  const getPersonaBadge = (persona: string) => {
    const p = persona.toLowerCase();
    switch (p) {
      case 'bolt':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-600/60 shadow-sm">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            Bolt ⚡
          </span>
        );
      case 'palette':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-600/60 shadow-sm">
            <Palette className="w-3.5 h-3.5 text-emerald-400" />
            Palette 🎨
          </span>
        );
      case 'sentinel':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-600/60 shadow-sm">
            <Shield className="w-3.5 h-3.5 text-rose-400" />
            Sentinel 🛡️
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-zinc-800 text-zinc-300 border border-zinc-700">
            {persona}
          </span>
        );
    }
  };

  return (
    <article className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 shadow-sm hover:border-zinc-700/80 transition-all flex flex-col justify-between">
      <div>
        {/* Card Header: Badges & Category */}
        <div className="flex items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            {getPersonaBadge(suggestion.persona)}
            <span className="text-xs uppercase font-mono tracking-wider px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700/60">
              {suggestion.category}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {onDiscard && (
              <button
                type="button"
                onClick={() => onDiscard(suggestion.id)}
                title="Scarta suggerimento"
                aria-label={`Scarta suggerimento ${suggestion.id}`}
                className="p-1 rounded text-zinc-500 hover:text-rose-400 hover:bg-zinc-800 transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            )}
            <span className="text-xs text-zinc-500 font-mono">
              {suggestion.id}
            </span>
          </div>
        </div>

        {/* Title */}
        <h3 className="text-base font-semibold text-zinc-100 mb-2 leading-snug">
          {suggestion.title}
        </h3>

        {/* File and Line */}
        <div className="flex items-center gap-1.5 text-xs text-zinc-400 font-mono mb-3 bg-zinc-950/60 px-2.5 py-1.5 rounded border border-zinc-800/80">
          <FileCode2 className="w-3.5 h-3.5 text-zinc-500 flex-shrink-0" />
          <span className="truncate">{suggestion.file}</span>
          <span className="text-zinc-600">::</span>
          <span className="text-zinc-300 font-semibold">L{suggestion.line}</span>
        </div>

        {/* Issue Description */}
        <p className="text-sm text-zinc-300 mb-2 line-clamp-2 leading-relaxed">
          {suggestion.issue}
        </p>

        {/* Impact */}
        <div className="text-xs text-zinc-400 mb-4 flex items-start gap-1.5">
          <strong className="text-zinc-200 flex-shrink-0">Impatto:</strong>
          <span className="text-zinc-400">{suggestion.impact}</span>
        </div>

        {/* Code Snippet Preview */}
        {suggestion.code_snippet && (
          <div className="mb-4">
            <div className="text-[11px] font-mono text-zinc-500 mb-1 flex items-center justify-between">
              <span>Frammento di codice</span>
              <span>&lt; 50 righe</span>
            </div>
            <pre className="p-3 bg-zinc-950 rounded border border-zinc-800/90 text-xs font-mono text-zinc-300 overflow-x-auto max-h-40 leading-tight">
              <code>{suggestion.code_snippet}</code>
            </pre>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="pt-3 border-t border-zinc-800/80 flex items-center justify-end gap-2.5">
        <button
          type="button"
          onClick={() => onEscalateToAntigravity(suggestion)}
          disabled={isEscalating || isRunning}
          title="Invia la patch ad Antigravity Senior Review via CDP (porta 9000)"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-zinc-800 text-zinc-200 border border-zinc-700 hover:bg-zinc-700/80 hover:text-white transition-colors disabled:opacity-50"
        >
          <Send className="w-3.5 h-3.5 text-zinc-400" />
          <span>Invia ad Antigravity (CDP 9000)</span>
        </button>

        <button
          type="button"
          onClick={() => onRunInJules(suggestion)}
          disabled={isRunning || isEscalating}
          title="Crea un worktree isolato ed esegui i test automatizzati"
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded text-xs font-semibold bg-zinc-100 text-zinc-950 hover:bg-white hover:shadow transition-colors disabled:opacity-50"
        >
          <Play className="w-3.5 h-3.5 fill-current" />
          <span>{isRunning ? 'Esecuzione...' : 'Run in Jules'}</span>
        </button>
      </div>
    </article>
  );
};

export const SuggestionSkeleton: React.FC = () => {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 animate-pulse flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex gap-2">
            <div className="h-5 w-20 bg-zinc-800 rounded-full" />
            <div className="h-5 w-16 bg-zinc-800 rounded" />
          </div>
          <div className="h-4 w-12 bg-zinc-800 rounded" />
        </div>
        <div className="h-6 w-3/4 bg-zinc-800 rounded mb-3" />
        <div className="h-8 w-full bg-zinc-950 rounded mb-3" />
        <div className="h-4 w-full bg-zinc-800/80 rounded mb-2" />
        <div className="h-4 w-2/3 bg-zinc-800/80 rounded mb-4" />
        <div className="h-24 w-full bg-zinc-950 rounded border border-zinc-800" />
      </div>
      <div className="pt-3 border-t border-zinc-800 flex justify-end gap-2 mt-4">
        <div className="h-7 w-32 bg-zinc-800 rounded" />
        <div className="h-7 w-24 bg-zinc-800 rounded" />
      </div>
    </div>
  );
};

export const SuggestionEmptyState: React.FC<{
  repoName?: string;
  onRefresh?: () => void;
}> = ({ repoName, onRefresh }) => {
  return (
    <div className="bg-zinc-900 border border-zinc-800 border-dashed rounded-lg p-10 text-center flex flex-col items-center justify-center">
      <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-400 mb-3">
        <Sparkles className="w-6 h-6 text-zinc-400" />
      </div>
      <h4 className="text-base font-semibold text-zinc-200 mb-1">
        Nessun suggerimento in sospeso
      </h4>
      <p className="text-sm text-zinc-400 max-w-md mb-4">
        {repoName
          ? `Il repository "${repoName}" non ha rilevato micro-miglioramenti da applicare.`
          : 'Nessun suggerimento attivo trovato per i filtri selezionati.'}
      </p>
      {onRefresh && (
        <button
          type="button"
          onClick={onRefresh}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-zinc-800 text-zinc-200 hover:bg-zinc-700 transition-colors"
        >
          <AlertCircle className="w-3.5 h-3.5 text-zinc-400" />
          Riesegui scansione
        </button>
      )}
    </div>
  );
};
