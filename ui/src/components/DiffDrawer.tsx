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
  ShieldCheck,
  GitPullRequest,
  ExternalLink,
} from 'lucide-react';
import { api, ApiError, useTaskLogs } from '../api';
import type {
  CreatePrResponse,
  SeniorReviewResult,
  TaskStatus,
} from '../types';

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
  initialReview?: SeniorReviewResult | null;
  onPrCreated?: (prUrl: string) => void;
  initialPrUrl?: string | null;
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
  initialReview = null,
  onPrCreated,
  initialPrUrl = null,
}) => {
  const [activeTab, setActiveTab] = useState<'diff' | 'logs'>('logs');
  const [copied, setCopied] = useState(false);
  const logTerminalEndRef = useRef<HTMLDivElement>(null);

  // Senior Review & PR state
  const [seniorReview, setSeniorReview] = useState<SeniorReviewResult | null>(initialReview);
  const [isReviewing, setIsReviewing] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [isCreatingPr, setIsCreatingPr] = useState(false);
  const [prResult, setPrResult] = useState<CreatePrResponse | null>(
    initialPrUrl
      ? { success: true, task_id: taskId || '', pr_url: initialPrUrl, message: 'Existing Pull Request' }
      : null
  );
  const [prError, setPrError] = useState<string | null>(null);

  // Hook for live SSE log streaming from /api/stream/{taskId}
  const { logs, status: liveStatus, isDone, error: streamError } = useTaskLogs(isOpen ? taskId : null);

  const effectiveStatus: TaskStatus = liveStatus !== 'pending' ? liveStatus : initialTaskStatus;

  // Sync initial review and clear state when taskId changes
  useEffect(() => {
    setSeniorReview(initialReview);
    setReviewError(null);
    if (initialPrUrl) {
      setPrResult({
        success: true,
        task_id: taskId || '',
        pr_url: initialPrUrl,
        message: 'Existing Pull Request',
      });
    } else {
      setPrResult(null);
    }
    setPrError(null);
  }, [taskId, initialReview, initialPrUrl]);

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

  const handleRequestSeniorReview = async () => {
    if (!taskId) return;
    setIsReviewing(true);
    setReviewError(null);
    try {
      const res = await api.runSeniorReview(taskId, diff || undefined);
      setSeniorReview(res);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.detail : 'Errore durante la richiesta di Senior Review.';
      setReviewError(msg);
    } finally {
      setIsReviewing(false);
    }
  };

  const handleCreatePr = async () => {
    if (!taskId || seniorReview?.verdict !== 'APPROVED') return;
    setIsCreatingPr(true);
    setPrError(null);
    try {
      const res = await api.createPullRequest(taskId);
      setPrResult(res);
      if (onPrCreated && res.pr_url) {
        onPrCreated(res.pr_url);
      }
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.detail : 'Errore durante la creazione della Pull Request.';
      setPrError(msg);
    } finally {
      setIsCreatingPr(false);
    }
  };

  const isApproved = seniorReview?.verdict === 'APPROVED';

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

      <div className="relative w-full max-w-3xl bg-[#0a0a0c] border-l border-zinc-800/80 flex flex-col h-full shadow-2xl z-10 animate-in slide-in-from-right duration-200">
        {/* Drawer Header */}
        <div className="p-4 border-b border-zinc-800/80 bg-[#101014] flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h2 className="text-base font-semibold text-zinc-100">
                Worktree Runner &amp; Diff Viewer
              </h2>
              {getStatusBadge(effectiveStatus)}
            </div>
            <div className="flex items-center gap-2 text-xs text-zinc-400 font-mono">
              <span>{repoName}</span>
              {branchName ? (
                <>
                  <span className="text-zinc-600">/</span>
                  <span className="text-zinc-300">{branchName}</span>
                </>
              ) : null}
              {taskId ? (
                <>
                  <span className="text-zinc-600">/</span>
                  <span className="text-zinc-400">{taskId}</span>
                </>
              ) : null}
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60 transition-colors"
            title="Chiudi pannello (Esc)"
            aria-label="Chiudi pannello"
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
              {logs.length > 0 ? (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-zinc-800 text-zinc-400 font-mono">
                  {logs.length}
                </span>
              ) : null}
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
              <span>Git Diff Micro-Patch &amp; Senior Gate</span>
              {diff ? (
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-emerald-950 text-emerald-300 font-mono">
                  attivo
                </span>
              ) : null}
            </button>
          </div>

          {activeTab === 'diff' && diff ? (
            <button
              type="button"
              onClick={handleCopyDiff}
              className="flex items-center gap-1 text-xs text-zinc-400 hover:text-zinc-200 transition-colors py-1 px-2 rounded bg-zinc-800/60"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copiato!' : 'Copia Diff'}</span>
            </button>
          ) : null}
        </div>

        {/* Tab Content Area */}
        <div className="flex-1 overflow-y-auto p-4 bg-zinc-950 font-mono text-xs space-y-4">
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
              {streamError ? (
                <div className="text-amber-400/90 py-2 text-xs font-sans">
                  {streamError}
                </div>
              ) : null}
              <div ref={logTerminalEndRef} />
            </div>
          ) : (
            <div className="space-y-4">
              {/* Diff Lines View */}
              {diff ? (
                <div className="border border-zinc-800/80 rounded bg-zinc-900/60 p-2 overflow-x-auto">
                  {renderDiffLines(diff)}
                </div>
              ) : (
                <div className="text-zinc-500 py-6 text-center italic">
                  Nessun file diff generato per questo task. Esegui la patch nel worktree per visualizzare le modifiche.
                </div>
              )}

              {/* Senior Review Gate Outcome Box */}
              {seniorReview ? (
                <div
                  className={`rounded-lg border p-4 font-sans space-y-3 ${
                    isApproved
                      ? 'bg-emerald-950/20 border-emerald-800/80 text-emerald-200'
                      : 'bg-rose-950/20 border-rose-800/80 text-rose-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-bold tracking-wide uppercase ${
                          isApproved
                            ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-600'
                            : 'bg-rose-900/80 text-rose-300 border border-rose-600'
                        }`}
                      >
                        {isApproved ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                        )}
                        Senior Verdict: {seniorReview.verdict}
                      </span>
                      <span className="text-xs text-zinc-400 font-mono">
                        Revisore: {seniorReview.reviewer_model}
                      </span>
                    </div>
                    {seniorReview.reviewed_at ? (
                      <span className="text-[11px] text-zinc-500 font-mono">
                        {new Date(seniorReview.reviewed_at).toLocaleTimeString()}
                      </span>
                    ) : null}
                  </div>

                  {/* Box "Spiegazione Semplice del Senior" */}
                  <div className="bg-zinc-950/90 rounded border border-zinc-800 p-3 space-y-2">
                    <div>
                      <h4 className="text-xs font-semibold text-zinc-200 uppercase tracking-wider">
                        Spiegazione Semplice del Senior
                      </h4>
                      <p className="text-xs text-zinc-300 mt-1 leading-relaxed whitespace-pre-wrap">
                        {seniorReview.simple_explanation}
                      </p>
                    </div>
                    <div className="pt-2 border-t border-zinc-800/80">
                      <h5 className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                        Note di Sicurezza
                      </h5>
                      <p className="text-xs text-zinc-300 mt-0.5 leading-relaxed">
                        {seniorReview.security_notes}
                      </p>
                    </div>
                  </div>
                </div>
              ) : null}

              {/* Review Error Notification */}
              {reviewError ? (
                <div className="p-3 bg-rose-950/40 border border-rose-800 rounded text-xs text-rose-300 flex items-center gap-2 font-sans">
                  <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                  <span>{reviewError}</span>
                </div>
              ) : null}

              {/* PR Success Notification */}
              {prResult ? (
                <div className="p-3 bg-emerald-950/50 border border-emerald-800 rounded text-xs text-emerald-200 flex items-center justify-between font-sans">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span>{prResult.message || 'Pull Request creata con successo!'}</span>
                  </div>
                  <a
                    href={prResult.pr_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 font-semibold underline text-emerald-300 hover:text-emerald-100"
                  >
                    <span>Apri PR</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              ) : null}

              {/* PR Error Notification */}
              {prError ? (
                <div className="p-3 bg-rose-950/40 border border-rose-800 rounded text-xs text-rose-300 flex items-center gap-2 font-sans">
                  <AlertTriangle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                  <span>{prError}</span>
                </div>
              ) : null}
            </div>
          )}
        </div>

        {/* Drawer Footer Actions */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-900/90 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleRequestSeniorReview}
              disabled={isReviewing || !taskId}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-zinc-800 text-zinc-100 hover:bg-zinc-700 border border-zinc-700 transition-colors disabled:opacity-50"
            >
              {isReviewing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-zinc-400" />
                  <span>Audit in corso...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Richiedi Audit Senior (In-Cockpit)</span>
                </>
              )}
            </button>

            {onEscalate ? (
              <button
                type="button"
                onClick={onEscalate}
                disabled={isEscalating}
                title="Invia al Senior su Antigravity IDE (Gemini 4 Argon Low / CDP :9000)"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-zinc-800 text-zinc-200 border border-zinc-700 hover:bg-zinc-700 transition-colors disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5 text-zinc-400" />
                <span>{isEscalating ? 'Inviando a CDP...' : 'Invia a Senior su Antigravity (Argon Low / CDP :9000)'}</span>
              </button>
            ) : null}
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCreatePr}
              disabled={!isApproved || isCreatingPr}
              title={
                !isApproved
                  ? 'La creazione della Pull Request richiede il verdetto APPROVED da parte del Senior Review'
                  : 'Apri una Pull Request su GitHub con il diff approvato'
              }
              className={`inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded text-xs font-semibold transition-colors ${
                isApproved
                  ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-sm'
                  : 'bg-zinc-800 text-zinc-500 border border-zinc-800 cursor-not-allowed opacity-60'
              }`}
            >
              {isCreatingPr ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Creazione PR...</span>
                </>
              ) : (
                <>
                  <GitPullRequest className="w-3.5 h-3.5" />
                  <span>Crea Pull Request</span>
                </>
              )}
            </button>

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
