import React, { useState } from 'react';
import {
  GitBranch,
  Trash2,
  Clock,
  FolderGit2,
  RefreshCw,
  Zap,
  Palette,
  Shield,
  Layers,
} from 'lucide-react';
import type { WorktreeSessionInfo } from '../types';

interface WorktreeListProps {
  worktrees: WorktreeSessionInfo[];
  onPrune: (worktreePath?: string) => Promise<void>;
  onRefresh: () => void;
  isLoading?: boolean;
}

export const WorktreeList: React.FC<WorktreeListProps> = ({
  worktrees,
  onPrune,
  onRefresh,
  isLoading = false,
}) => {
  const [pruningPath, setPruningPath] = useState<string | null>(null);
  const [isPruningAll, setIsPruningAll] = useState<boolean>(false);

  const handlePruneSingle = async (path: string) => {
    try {
      setPruningPath(path);
      await onPrune(path);
    } finally {
      setPruningPath(null);
    }
  };

  const handlePruneAll = async () => {
    try {
      setIsPruningAll(true);
      await onPrune();
    } finally {
      setIsPruningAll(false);
    }
  };

  const formatAge = (createdAtStr?: string | null) => {
    if (!createdAtStr) return 'recente';
    try {
      const created = new Date(createdAtStr);
      const now = new Date();
      const diffMs = now.getTime() - created.getTime();
      const diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return '< 1 min fa';
      if (diffMins === 1) return '1 min fa';
      if (diffMins < 60) return `${diffMins} min fa`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours === 1) return '1 ora fa';
      return `${diffHours} ore fa`;
    } catch {
      return createdAtStr;
    }
  };

  const getPersonaIcon = (persona: string) => {
    const p = persona.toLowerCase();
    switch (p) {
      case 'bolt':
        return <Zap className="w-3.5 h-3.5 text-amber-400" />;
      case 'palette':
        return <Palette className="w-3.5 h-3.5 text-emerald-400" />;
      case 'sentinel':
        return <Shield className="w-3.5 h-3.5 text-rose-400" />;
      default:
        return <Layers className="w-3.5 h-3.5 text-zinc-400" />;
    }
  };

  return (
    <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-zinc-400" />
          <h2 className="text-sm font-semibold text-zinc-100 uppercase tracking-wider">
            Worktree Attivi
          </h2>
          <span className="px-2 py-0.5 rounded-full text-xs font-mono font-medium bg-zinc-800 text-zinc-300">
            {worktrees.length}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onRefresh}
            disabled={isLoading}
            className="p-1.5 rounded text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors disabled:opacity-50"
            title="Aggiorna lista worktree"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          {worktrees.length > 0 && (
            <button
              type="button"
              onClick={handlePruneAll}
              disabled={isPruningAll}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium bg-zinc-800 text-rose-300 border border-zinc-700/80 hover:bg-rose-950/40 hover:border-rose-700/60 transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-3.5 h-3.5 text-rose-400" />
              <span>{isPruningAll ? 'Pulizia...' : 'Prune All'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Content list or empty state */}
      {worktrees.length === 0 ? (
        <div className="py-6 text-center text-xs text-zinc-500 border border-dashed border-zinc-800/80 rounded">
          Nessun worktree attivo al momento. I worktree isolati vengono creati durante l'esecuzione dei compiti di cura e rimossi automaticamente.
        </div>
      ) : (
        <div className="space-y-2.5">
          {worktrees.map((wt) => {
            const isPruning = pruningPath === wt.worktree_path;

            return (
              <div
                key={wt.worktree_path}
                className="bg-zinc-950/70 border border-zinc-800/80 rounded-md p-3 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1 min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-zinc-200 flex items-center gap-1.5">
                      <FolderGit2 className="w-3.5 h-3.5 text-zinc-400" />
                      {wt.repo_name}
                    </span>

                    <span className="font-mono text-zinc-400 px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700/50">
                      {wt.branch}
                    </span>

                    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[11px] font-medium bg-zinc-900 border border-zinc-800 text-zinc-300">
                      {getPersonaIcon(wt.persona)}
                      <span className="capitalize">{wt.persona}</span>
                    </span>
                  </div>

                  <div className="text-zinc-500 font-mono truncate text-[11px]">
                    {wt.worktree_path}
                  </div>
                </div>

                <div className="flex items-center gap-4 flex-shrink-0">
                  <div className="flex items-center gap-1 text-zinc-400 text-[11px]">
                    <Clock className="w-3 h-3 text-zinc-500" />
                    <span>{formatAge(wt.created_at)}</span>
                  </div>

                  <button
                    type="button"
                    onClick={() => handlePruneSingle(wt.worktree_path)}
                    disabled={isPruning}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium bg-zinc-800 text-zinc-300 hover:text-rose-300 hover:bg-rose-950/30 border border-zinc-700 hover:border-rose-700/50 transition-colors disabled:opacity-50"
                    title="Rimuovi questo worktree e rilascia il lock git"
                  >
                    <Trash2 className="w-3 h-3 text-zinc-400" />
                    <span>{isPruning ? 'Pruning...' : 'Prune'}</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
};
