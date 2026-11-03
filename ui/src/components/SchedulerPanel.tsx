import React, { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Play,
  Clock,
  CheckCircle2,
  Save,
  RefreshCw,
} from 'lucide-react';
import type { HubConfig, RepoScheduleConfig } from '../types';
import { api, ApiError } from '../api';

interface SchedulerPanelProps {
  compact?: boolean;
  selectedRepo?: string;
  onTriggerRepo?: (repoName: string) => void;
}

export const SchedulerPanel: React.FC<SchedulerPanelProps> = ({
  compact = false,
  selectedRepo,
  onTriggerRepo,
}) => {
  const [config, setConfig] = useState<HubConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [triggeringRepo, setTriggeringRepo] = useState<string | null>(null);
  const [triggerMessage, setTriggerMessage] = useState<{ repo: string; text: string; success: boolean } | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const cfg = await api.getConfig();
      setConfig(cfg);
    } catch (err) {
      console.error('Failed to load scheduler data', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleTrigger = async (repoName: string) => {
    setTriggeringRepo(repoName);
    setTriggerMessage(null);
    try {
      const res = await api.triggerScheduler(repoName);
      if (onTriggerRepo) {
        onTriggerRepo(repoName);
      }
      setTriggerMessage({
        repo: repoName,
        text: `Curazione per '${res.repo_name}' avviata con successo!`,
        success: true,
      });

      const updatedConfig = await api.getConfig();
      setConfig(updatedConfig);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.detail : 'Avvio schedulazione fallito';
      setTriggerMessage({
        repo: repoName,
        text: msg,
        success: false,
      });
    } finally {
      setTriggeringRepo(null);
      setTimeout(() => setTriggerMessage(null), 5000);
    }
  };

  const handleToggleSchedule = (repoName: string) => {
    if (!config) return;
    setConfig({
      ...config,
      repo_schedules: config.repo_schedules.map((s) =>
        s.repo_name === repoName ? { ...s, enabled: !s.enabled } : s
      ),
    });
  };

  const handleIntervalChange = (repoName: string, hours: number) => {
    if (!config) return;
    setConfig({
      ...config,
      repo_schedules: config.repo_schedules.map((s) =>
        s.repo_name === repoName ? { ...s, interval_hours: hours } : s
      ),
    });
  };

  const handleTogglePersona = (repoName: string, persona: string) => {
    if (!config) return;
    setConfig({
      ...config,
      repo_schedules: config.repo_schedules.map((s) => {
        if (s.repo_name !== repoName) return s;
        const exists = s.personas.includes(persona);
        if (exists && s.personas.length === 1) return s;
        const updated = exists
          ? s.personas.filter((p) => p !== persona)
          : [...s.personas, persona];
        return { ...s, personas: updated };
      }),
    });
  };

  const handleSaveSchedules = async () => {
    if (!config) return;
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await api.updateConfig(config);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to save schedules', err);
    } finally {
      setIsSaving(false);
    }
  };

  const formatTimestamp = (iso?: string | null) => {
    if (!iso) return 'Never';
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' (' + d.toLocaleDateString([], { day: '2-digit', month: '2-digit' }) + ')';
    } catch {
      return iso;
    }
  };

  if (isLoading || !config) {
    return (
      <div className="py-8 px-4 text-center text-zinc-400 flex items-center justify-center gap-2">
        <RefreshCw className="w-4 h-4 animate-spin text-zinc-400" />
        <span className="text-xs">Loading schedules...</span>
      </div>
    );
  }

  // Filter schedules if compact and selectedRepo is provided
  const activeSchedules = config.repo_schedules.filter(
    (s) => !selectedRepo || s.repo_name === selectedRepo || !compact
  );

  const hasAnyActiveSchedules = config.repo_schedules.some((s) => s.enabled);

  // If compact and no enabled schedule matches, show empty state matching Screenshot 3 & 5
  if (compact && (!hasAnyActiveSchedules || activeSchedules.length === 0)) {
    return (
      <div className="py-10 px-4 text-center flex flex-col items-center justify-center rounded-xl bg-zinc-900/30 border border-dashed border-zinc-800/80">
        <div className="w-10 h-10 rounded-full bg-zinc-800/80 flex items-center justify-center text-zinc-400 mb-3">
          <Clock className="w-5 h-5 text-zinc-400" />
        </div>
        <h4 className="text-sm font-semibold text-zinc-200 mb-1">
          No scheduled tasks yet
        </h4>
        <p className="text-xs text-zinc-400 max-w-sm mb-4">
          Schedule tasks to run automatically at specific times.
        </p>
        <button
          type="button"
          onClick={() => {
            if (selectedRepo && !config.repo_schedules.some((s) => s.repo_name === selectedRepo)) {
              const newSched: RepoScheduleConfig = {
                repo_name: selectedRepo,
                enabled: true,
                interval_hours: 6,
                personas: ['bolt', 'palette', 'sentinel'],
                max_pending_worktrees: 3,
                last_run_at: null,
                next_run_at: null,
              };
              setConfig({
                ...config,
                repo_schedules: [...config.repo_schedules, newSched],
              });
            }
          }}
          className="px-3 py-1.5 min-h-[36px] rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium transition-colors"
        >
          Enable scheduler for {selectedRepo || 'repo'}
        </button>
      </div>
    );
  }

  // Compact row representation inside central card
  if (compact) {
    return (
      <div className="space-y-3">
        {triggerMessage && (
          <div
            className={`p-2.5 rounded-lg text-xs flex items-center gap-2 border ${
              triggerMessage.success
                ? 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
                : 'bg-rose-950/40 text-rose-300 border-rose-800/60'
            }`}
          >
            <span>{triggerMessage.text}</span>
          </div>
        )}

        <div className="space-y-2">
          {activeSchedules.map((sched) => {
            const isTriggering = triggeringRepo === sched.repo_name;
            return (
              <div
                key={sched.repo_name}
                className="flex items-center justify-between p-3 rounded-lg bg-[#101014] border border-zinc-800/80 gap-3"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <input
                    type="checkbox"
                    checked={sched.enabled}
                    onChange={() => handleToggleSchedule(sched.repo_name)}
                    className="w-4 h-4 rounded bg-zinc-900 border-zinc-700 text-[#8b5cf6] focus:ring-[#8b5cf6] cursor-pointer"
                  />
                  <div className="min-w-0">
                    <span className="text-xs font-semibold text-zinc-100 block truncate">
                      {sched.repo_name}
                    </span>
                    <span className="text-[11px] text-zinc-400">
                      Every {sched.interval_hours}h • Last run: {formatTimestamp(sched.last_run_at)}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <button
                    type="button"
                    onClick={() => handleTrigger(sched.repo_name)}
                    disabled={isTriggering || !sched.enabled}
                    className="px-3 py-1.5 min-h-[36px] rounded-md bg-zinc-800 hover:bg-zinc-700 text-zinc-100 text-xs font-medium transition-colors disabled:opacity-50"
                  >
                    {isTriggering ? 'Running...' : 'Run now'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  // Full view (used if rendered standalone)
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6 text-zinc-200">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-[#a78bfa]" />
            <span>Autonomous Repository Scheduler</span>
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Periodic code health & curation scanner for local codebases.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {saveSuccess && (
            <span className="text-xs px-2.5 py-1 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800 flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Schedules saved!
            </span>
          )}

          <button
            type="button"
            onClick={handleSaveSchedules}
            disabled={isSaving}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 min-h-[44px] bg-[#8b5cf6] hover:bg-[#7c3aed] text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
          >
            {isSaving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            <span>{isSaving ? 'Saving...' : 'Save Schedules'}</span>
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {config.repo_schedules.map((sched) => {
          const isTriggering = triggeringRepo === sched.repo_name;

          return (
            <div
              key={sched.repo_name}
              className={`bg-[#141419] border rounded-xl p-5 transition-all ${
                sched.enabled ? 'border-zinc-800 shadow-sm' : 'border-zinc-800/60 opacity-75'
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800/80 pb-3">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={sched.enabled}
                    onChange={() => handleToggleSchedule(sched.repo_name)}
                    className="rounded bg-zinc-950 border-zinc-700 text-[#8b5cf6] focus:ring-0 cursor-pointer h-4 w-4"
                  />
                  <div>
                    <span className="text-base font-bold text-zinc-100">
                      {sched.repo_name}
                    </span>
                    <span
                      className={`ml-2 text-[10px] uppercase font-semibold px-2 py-0.5 rounded tracking-wide ${
                        sched.enabled
                          ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
                          : 'bg-zinc-800 text-zinc-400 border border-zinc-700/60'
                      }`}
                    >
                      {sched.enabled ? 'Active' : 'Paused'}
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleTrigger(sched.repo_name)}
                  disabled={isTriggering || !sched.enabled}
                  className="inline-flex items-center gap-1.5 px-3.5 py-1.5 min-h-[36px] rounded text-xs font-semibold bg-zinc-100 text-zinc-950 hover:bg-white transition-colors disabled:opacity-50"
                >
                  {isTriggering ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Play className="w-3.5 h-3.5 fill-current" />
                  )}
                  <span>{isTriggering ? 'Running...' : 'Run Now'}</span>
                </button>
              </div>

              <div className="pt-3 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                <div>
                  <label className="block text-[11px] text-zinc-400 mb-1">
                    Interval
                  </label>
                  <select
                    value={sched.interval_hours}
                    onChange={(e) => handleIntervalChange(sched.repo_name, Number(e.target.value))}
                    className="w-full bg-[#101014] border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-zinc-200 focus:outline-none"
                  >
                    <option value={6}>Every 6 hours</option>
                    <option value={12}>Every 12 hours</option>
                    <option value={24}>Every 24 hours</option>
                  </select>
                </div>

                <div>
                  <span className="block text-[11px] text-zinc-400 mb-1">
                    Active Personas
                  </span>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {(['bolt', 'palette', 'sentinel'] as const).map((p) => {
                      const active = sched.personas.includes(p);
                      return (
                        <button
                          key={p}
                          type="button"
                          onClick={() => handleTogglePersona(sched.repo_name, p)}
                          className={`px-2 py-0.5 rounded text-[11px] font-semibold border transition-colors ${
                            active
                              ? 'bg-[#2e2348] text-[#c4b5fd] border-[#8b5cf6]/60'
                              : 'bg-zinc-900 text-zinc-400 border-zinc-800'
                          }`}
                        >
                          {p.toUpperCase()}
                        </button>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <span className="block text-[11px] text-zinc-400 mb-1">
                    Execution Status
                  </span>
                  <p className="text-[11px] text-zinc-300">
                    Last: {formatTimestamp(sched.last_run_at)}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
