import React, { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Play,
  Clock,
  CheckCircle2,
  AlertCircle,
  Save,
  Plus,
  RefreshCw,
  Zap,
  Palette,
  Shield,
  Layers,
} from 'lucide-react';
import type { HubConfig, ProjectInfo, RepoScheduleConfig } from '../types';
import { api, ApiError } from '../api';

interface SchedulerPanelProps {
  onTriggerRepo?: (repoName: string) => void;
}

export const SchedulerPanel: React.FC<SchedulerPanelProps> = ({ onTriggerRepo }) => {
  const [config, setConfig] = useState<HubConfig | null>(null);
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [triggeringRepo, setTriggeringRepo] = useState<string | null>(null);
  const [triggerMessage, setTriggerMessage] = useState<{ repo: string; text: string; success: boolean } | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // New repo schedule selector
  const [selectedNewRepo, setSelectedNewRepo] = useState<string>('');

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const [cfg, projs] = await Promise.allSettled([
        api.getConfig(),
        api.getProjects(),
      ]);

      let loadedConfig: HubConfig | null = null;
      if (cfg.status === 'fulfilled') {
        loadedConfig = cfg.value;
      }

      let loadedProjects: ProjectInfo[] = [];
      if (projs.status === 'fulfilled') {
        loadedProjects = projs.value;
        setProjects(loadedProjects);
      }

      if (loadedConfig) {
        // If repo_schedules is empty, seed defaults from loaded projects or 'jules'
        if (loadedConfig.repo_schedules.length === 0) {
          const defaultNames = loadedProjects.length > 0
            ? loadedProjects.slice(0, 3).map((p) => p.name)
            : ['jules'];

          loadedConfig.repo_schedules = defaultNames.map((name) => ({
            repo_name: name,
            enabled: true,
            interval_hours: 6,
            personas: ['bolt', 'palette', 'sentinel'],
            max_pending_worktrees: 3,
            last_run_at: null,
            next_run_at: null,
          }));
        }
        setConfig(loadedConfig);
      }
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

      // Reload config to get updated last_run_at and next_run_at
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
        if (exists && s.personas.length === 1) {
          // Keep at least one persona
          return s;
        }
        const updated = exists
          ? s.personas.filter((p) => p !== persona)
          : [...s.personas, persona];
        return { ...s, personas: updated };
      }),
    });
  };

  const handleMaxWorktreesChange = (repoName: string, val: number) => {
    if (!config) return;
    const clamped = Math.max(1, Math.min(10, val));
    setConfig({
      ...config,
      repo_schedules: config.repo_schedules.map((s) =>
        s.repo_name === repoName ? { ...s, max_pending_worktrees: clamped } : s
      ),
    });
  };

  const handleAddRepoSchedule = () => {
    if (!config || !selectedNewRepo) return;
    const alreadyExists = config.repo_schedules.some((s) => s.repo_name === selectedNewRepo);
    if (alreadyExists) return;

    const newSched: RepoScheduleConfig = {
      repo_name: selectedNewRepo,
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
    setSelectedNewRepo('');
  };

  const handleSaveSchedules = async () => {
    if (!config) return;
    setIsSaving(true);
    try {
      await api.updateConfig(config);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to save scheduler config', err);
    } finally {
      setIsSaving(false);
    }
  };

  const formatTimestamp = (iso?: string | null) => {
    if (!iso) return 'Mai';
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' (' + d.toLocaleDateString([], { day: '2-digit', month: '2-digit' }) + ')';
    } catch {
      return iso;
    }
  };

  if (isLoading || !config) {
    return (
      <div className="max-w-5xl mx-auto p-6 text-zinc-400 flex items-center gap-2">
        <RefreshCw className="w-4 h-4 animate-spin text-zinc-500" />
        <span>Caricamento pianificazione autonoma repository...</span>
      </div>
    );
  }

  // Filter projects not yet in schedule
  const availableProjectsToAdd = projects.filter(
    (p) => !config.repo_schedules.some((s) => s.repo_name === p.name)
  );

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6 text-zinc-200">
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-indigo-400" />
            <span>Autonomous Repository Scheduler</span>
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Pianificazione di scan periodici per-repository con guardrail di sicurezza max-pending-worktrees.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {saveSuccess ? (
            <span className="text-xs px-2.5 py-1 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-800 flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Pianificazioni salvate!
            </span>
          ) : null}

          <button
            type="button"
            onClick={handleSaveSchedules}
            disabled={isSaving}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold transition-colors disabled:opacity-50"
          >
            {isSaving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            <span>{isSaving ? 'Salvataggio...' : 'Salva Pianificazioni'}</span>
          </button>
        </div>
      </div>

      {/* Global Status Message if any */}
      {triggerMessage ? (
        <div
          className={`p-3 rounded-lg border text-xs flex items-center gap-2 ${
            triggerMessage.success
              ? 'bg-emerald-950/50 border-emerald-800 text-emerald-300'
              : 'bg-rose-950/50 border-rose-800 text-rose-300'
          }`}
        >
          {triggerMessage.success ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
          )}
          <span>{triggerMessage.text}</span>
        </div>
      ) : null}

      {/* Add Repository to Scheduler Bar */}
      {availableProjectsToAdd.length > 0 ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3.5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-zinc-400" />
            <span className="text-xs font-medium text-zinc-300">
              Aggiungi repository alla pianificazione:
            </span>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedNewRepo}
              onChange={(e) => setSelectedNewRepo(e.target.value)}
              className="bg-zinc-950 border border-zinc-800 rounded px-3 py-1.5 text-xs text-zinc-200 focus:outline-none"
            >
              <option value="">Seleziona repository...</option>
              {availableProjectsToAdd.map((p) => (
                <option key={p.name} value={p.name}>
                  {p.name}
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={handleAddRepoSchedule}
              disabled={!selectedNewRepo}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded text-xs font-medium border border-zinc-700 transition-colors disabled:opacity-50"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Aggiungi</span>
            </button>
          </div>
        </div>
      ) : null}

      {/* Repository Schedule Cards List */}
      <div className="space-y-4">
        {config.repo_schedules.map((sched) => {
          const isTriggering = triggeringRepo === sched.repo_name;

          return (
            <div
              key={sched.repo_name}
              className={`bg-zinc-900 border rounded-lg p-5 transition-all ${
                sched.enabled ? 'border-zinc-800 shadow-sm' : 'border-zinc-800/60 opacity-75'
              }`}
            >
              {/* Row 1: Repo Title, Status Toggle, and Run Button */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-zinc-800/80 pb-3">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id={`toggle-${sched.repo_name}`}
                    checked={sched.enabled}
                    onChange={() => handleToggleSchedule(sched.repo_name)}
                    className="rounded bg-zinc-950 border-zinc-700 text-indigo-500 focus:ring-0 cursor-pointer h-4 w-4"
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <label
                        htmlFor={`toggle-${sched.repo_name}`}
                        className={`text-base font-bold cursor-pointer ${
                          sched.enabled ? 'text-zinc-100' : 'text-zinc-400 line-through'
                        }`}
                      >
                        {sched.repo_name}
                      </label>
                      <span
                        className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded tracking-wide ${
                          sched.enabled
                            ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
                            : 'bg-zinc-800 text-zinc-500 border border-zinc-700/60'
                        }`}
                      >
                        {sched.enabled ? 'Attivo' : 'In Pausa'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={() => handleTrigger(sched.repo_name)}
                    disabled={isTriggering || !sched.enabled}
                    title="Avvia manualmente un ciclo di scansione e curazione autonomo"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-semibold bg-zinc-100 text-zinc-950 hover:bg-white transition-colors disabled:opacity-50"
                  >
                    {isTriggering ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Play className="w-3.5 h-3.5 fill-current" />
                    )}
                    <span>{isTriggering ? 'Esecuzione...' : 'Esegui Ora'}</span>
                  </button>
                </div>
              </div>

              {/* Row 2: Interval, Personas, Max Pending, and Timestamps */}
              <div className="pt-3 grid grid-cols-1 md:grid-cols-4 gap-4 text-xs">
                {/* Interval Dropdown */}
                <div>
                  <label htmlFor={`interval-${sched.repo_name}`} className="block text-[11px] text-zinc-400 mb-1 flex items-center gap-1">
                    <Clock className="w-3 h-3 text-zinc-500" />
                    <span>Intervallo Esecuzione</span>
                  </label>
                  <select
                    id={`interval-${sched.repo_name}`}
                    value={sched.interval_hours}
                    onChange={(e) => handleIntervalChange(sched.repo_name, Number(e.target.value))}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-zinc-200 focus:outline-none"
                  >
                    <option value={6}>Ogni 6 ore</option>
                    <option value={12}>Ogni 12 ore</option>
                    <option value={24}>Ogni 24 ore (1 giorno)</option>
                  </select>
                </div>

                {/* Personas Toggle */}
                <div>
                  <span className="block text-[11px] text-zinc-400 mb-1">
                    Personas Abilitate
                  </span>
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <button
                      type="button"
                      onClick={() => handleTogglePersona(sched.repo_name, 'bolt')}
                      title="Toggle Persona Bolt"
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold border transition-colors ${
                        sched.personas.includes('bolt')
                          ? 'bg-amber-950/80 text-amber-300 border-amber-600/70'
                          : 'bg-zinc-950 text-zinc-500 border-zinc-800 hover:text-zinc-400'
                      }`}
                    >
                      <Zap className="w-3 h-3 text-amber-400" />
                      <span>Bolt ⚡</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleTogglePersona(sched.repo_name, 'palette')}
                      title="Toggle Persona Palette"
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold border transition-colors ${
                        sched.personas.includes('palette')
                          ? 'bg-emerald-950/80 text-emerald-300 border-emerald-600/70'
                          : 'bg-zinc-950 text-zinc-500 border-zinc-800 hover:text-zinc-400'
                      }`}
                    >
                      <Palette className="w-3 h-3 text-emerald-400" />
                      <span>Palette 🎨</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => handleTogglePersona(sched.repo_name, 'sentinel')}
                      title="Toggle Persona Sentinel"
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold border transition-colors ${
                        sched.personas.includes('sentinel')
                          ? 'bg-rose-950/80 text-rose-300 border-rose-600/70'
                          : 'bg-zinc-950 text-zinc-500 border-zinc-800 hover:text-zinc-400'
                      }`}
                    >
                      <Shield className="w-3 h-3 text-rose-400" />
                      <span>Sentinel 🛡️</span>
                    </button>
                  </div>
                </div>

                {/* Max Pending Worktrees */}
                <div>
                  <label htmlFor={`max-worktrees-${sched.repo_name}`} className="block text-[11px] text-zinc-400 mb-1">
                    Max Worktrees Sospesi
                  </label>
                  <input
                    id={`max-worktrees-${sched.repo_name}`}
                    type="number"
                    min={1}
                    max={10}
                    value={sched.max_pending_worktrees}
                    onChange={(e) => handleMaxWorktreesChange(sched.repo_name, Number(e.target.value))}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-zinc-200 focus:outline-none"
                  />
                </div>

                {/* Last Run & Next Run Status */}
                <div className="bg-zinc-950/60 rounded p-2 border border-zinc-800/80 space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-zinc-500">Ultimo Scan:</span>
                    <span className="font-mono text-zinc-300">
                      {formatTimestamp(sched.last_run_at)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="text-zinc-500">Prossimo:</span>
                    <span className="font-mono text-zinc-300">
                      {formatTimestamp(sched.next_run_at)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
