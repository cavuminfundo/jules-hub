import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Terminal,
  FileDiff,
  Send,
  Copy,
  Check,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Loader2,
} from 'lucide-react';
import { useTaskLogs } from '../api';
import type { TaskStatus } from '../types';

interface DiffDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  taskId: string | null;
  diff: string | null;
  taskStatus: TaskStatus;
  repoName: string;
  branchName?: string;
  onEscalate?: () => void;
  isEscalating?: boolean;
}

export const DiffDrawer: React.FC<DiffDrawerProps> = ({
  isOpen,
  onClose,
  taskId,
  diff,
  taskStatus: initialTaskStatus,
  repoName,
  branchName,
  onEscalate,
  isEscalating = false,
}) => {
  const [activeTab, setActiveTab] = useState<'diff' | 'logs'>('logs');
  const [copied, setCopied] = useState(false);
  const logTerminalEndRef = useRef<HTMLDivElement>(null);

  // Hook for live SSE log streaming from /api/stream/{taskId}
  const { logs, status: liveStatus, isDone, error: streamError } = useTaskLogs(isOpen ? taskId : null);

  const effectiveStatus: TaskStatus = liveStatus !== 'pending' ? liveStatus : initialTaskStatus;

  // Auto-scroll terminal when new logs arrive
  useEffect(() => {
    if (activeTab === 'logs' && logTerminalEndRef.current) {
      logTerminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, activeTab]);

  // Switch to diff tab automatically if diff is available and task finishes
  useEffect(() => {
    if (diff && isDone) {
      setActiveTab('diff');
    }
  }, [diff, isDone]);

  // Esc key listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleCopyDiff = () => {
    if (diff) {
      navigator.clipboard.writeText(diff);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getStatusBadge = (status: TaskStatus) => {
    switch (status) {
      case 'running':
      case 'testing':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-600/60">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
            {status === 'testing' ? 'Esecuzione Test...' : 'In Elaborazione...'}
          </span>
        );
      case 'passed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-600/60">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            Test Superati (PASSED)
          </span>
        );
      case 'needs_escalation':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold bg-amber-950/80 text-amber-300 border border-amber-600/60">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            Richiede Review Senior
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold bg-rose-950/80 text-rose-300 border border-rose-600/60">
            <XCircle className="w-3.5 h-3.5 text-rose-400" />
            Fallito (FAILED)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-medium bg-zinc-800 text-zinc-300">
            {status}
          </span>
        );
    }
  };

  // Colorized diff line renderer
  const renderDiffLines = (rawDiff: string) => {
    const lines = rawDiff.split('\n');
    return lines.map((line, idx) => {
      let lineStyle = 'text-zinc-300 pl-3';
      if (line.startsWith('+++') || line.startsWith('---')) {
        lineStyle = 'text-zinc-400 font-semibold bg-zinc-900 pl-2';
      } else if (line.startsWith('+')) {
        lineStyle = 'bg-emerald-950/50 text-emerald-200 border-l-2 border-emerald-500 pl-2';
      } else if (line.startsWith('-')) {
        lineStyle = 'bg-rose-950/50 text-rose-200 border-l-2 border-rose-500 pl-2';
      } else if (line.startsWith('@@')) {
        lineStyle = 'bg-zinc-800/60 text-zinc-400 font-medium pl-2 text-xs py-0.5 my-0.5';
      }

      return (
        <div key={idx} className={`font-mono text-xs whitespace-pre py-0.5 ${lineStyle}`}>
          {line || ' '}
        </div>
      );
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
      <div
        className="fixed inset-0"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="relative w-full max-w-3xl bg-zinc-950 border-l border-zinc-800 flex flex-col h-full shadow-2xl z-10 animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="p-4 border-b border-zinc-800 bg-zinc-900/90 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-base font-semibold text-zinc-100">
                Worktree Runner &amp; Diff Viewer
              </h2>
              {getStatusBadge(effectiveStatus)}
            </div>
            <div className="flex items-center gap-2 text-xs text-zinc-400 font-mono">
              <span>{repoName}</span>
              {branchName && (
                <>
                  <span className="text-zinc-600">/</span>
                  <span className="text-zinc-300">{branchName}</span>
                </>
              )}
              {taskId && (
                <>
                  <span className="text-zinc-600">/</span>
                  <span className="text-zinc-500">{taskId}</span>
                </>
              )}
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-md text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800 transition-colors"
            title="Chiudi pannello (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center justify-between px-4 border-b border-zinc-800 bg-zinc-900/40">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setActiveTab('logs')}
              className={`flex items-center gap-1.5 py-2.5 px-3 border-b-2 text-xs font-medium transition-colors ${
                activeTab === 'logs'
                  ? 'border-zinc-100 text-zinc-100'
                  : 'border-transparent text-zinc-400 hover:text-zinc-300'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Console Log (Live SSE)</span>
              {logs.length > 0 && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-zinc-800 text-zinc-400 font-mono">
                  {logs.length}
                </span>
              )}
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('diff')}
              className={`flex items-center gap-1.5 py-2.5 px-3 border-b-2 text-xs font-medium transition-colors ${
                activeTab === 'diff'
                  ? 'border-zinc-100 text-zinc-100'
                  : 'border-transparent text-zinc-400 hover:text-zinc-300'
              }`}
            >
              <FileDiff className="w-3.5 h-3.5" />
              <span>Git Diff Micro-Patch</span>
              {diff && (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-950 text-emerald-300 font-mono">
                  attivo
                </span>
              )}
            </button>
          </div>

          {activeTab === 'diff' && diff && (
            <button
              type="button"
              onClick={handleCopyDiff}
              className="flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors py-1 px-2 rounded bg-zinc-800/60"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copiato!' : 'Copia Diff'}</span>
            </button>
          )}
        </div>

        {/* Tab Content Area */}
        <div className="flex-1 overflow-y-auto p-4 bg-zinc-950 font-mono text-xs">
          {activeTab === 'logs' ? (
            <div className="space-y-1">
              {logs.length === 0 ? (
                <div className="text-zinc-500 py-6 text-center italic">
                  In attesa di eventi dallo stream SSE...
                </div>
              ) : (
                logs.map((log, index) => (
                  <div key={index} className="text-zinc-300 leading-relaxed break-words whitespace-pre-wrap">
                    <span className="text-zinc-600 select-none mr-2">{String(index + 1).padStart(2, '0')}</span>
                    {log}
                  </div>
                ))
              )}
              {streamError && (
                <div className="text-amber-400/90 py-2 text-xs">
                  {streamError}
                </div>
              )}
              <div ref={logTerminalEndRef} />
            </div>
          ) : (
            <div>
              {diff ? (
                <div className="border border-zinc-800/80 rounded bg-zinc-900/60 p-2 overflow-x-auto">
                  {renderDiffLines(diff)}
                </div>
              ) : (
                <div className="text-zinc-500 py-10 text-center italic">
                  Nessun file diff generato per questo task. Esegui la patch nel worktree per visualizzare le modifiche.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Drawer Footer Actions */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-900/80 flex items-center justify-between">
          <div className="text-xs text-zinc-500">
            {isDone ? 'Task completato' : 'In esecuzione nel worktree isolato'}
          </div>

          <div className="flex items-center gap-3">
            {onEscalate && (
              <button
                type="button"
                onClick={onEscalate}
                disabled={isEscalating}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-zinc-100 text-zinc-950 hover:bg-white transition-colors disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5 text-zinc-950" />
                <span>{isEscalating ? 'Inviando a CDP...' : 'Invia ad Antigravity (CDP 9000)'}</span>
              </button>
            )}

            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 rounded text-xs font-medium bg-zinc-800 text-zinc-200 hover:bg-zinc-700 transition-colors"
            >
              Chiudi
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
