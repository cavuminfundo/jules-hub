import React, { useState, useEffect, useCallback } from 'react';
import {
  Save,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Cpu,
  ShieldCheck,
  Plus,
  Trash2,
  Server,
  Sliders,
} from 'lucide-react';
import type { HubConfig, OllamaInstance, OllamaProbeResult } from '../types';
import { api, ApiError } from '../api';

interface SettingsViewProps {
  onSaveConfig?: (cfg: HubConfig) => void;
}

const DEFAULT_CONFIG: HubConfig = {
  ollama_instances: [
    {
      id: 1,
      name: 'GPU Server 24/7',
      url: 'http://192.168.88.117:11434',
      enabled: true,
      timeout_sec: 30,
    },
    {
      id: 2,
      name: 'Workstation RTX 5070 Ti',
      url: 'http://100.102.204.70:11434',
      enabled: true,
      timeout_sec: 15,
    },
  ],
  junior_config: {
    provider: 'ollama',
    instance_id: 1,
    model_name: 'qwen2.5-coder',
    fallback_provider: 'antigravity_cli',
    fallback_instance_id: undefined,
    fallback_model: 'flash',
  },
  senior_config: {
    provider: 'cdp',
    instance_id: 1,
    model_name: 'Gemini 4 Argon (Low)',
    fallback_provider: undefined,
    fallback_instance_id: undefined,
    fallback_model: undefined,
  },
  senior_mode: 'cdp',
  cdp_host: '127.0.0.1',
  cdp_port: 9000,
  max_diff_lines: 50,
  repo_schedules: [],
};

export const SettingsView: React.FC<SettingsViewProps> = ({ onSaveConfig }) => {
  const [config, setConfig] = useState<HubConfig | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [testingId, setTestingId] = useState<number | null>(null);
  const [testResults, setTestResults] = useState<Record<number, OllamaProbeResult>>({});
  const [cdpModels, setCdpModels] = useState<string[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<{ success: boolean; message: string } | null>(null);

  // New instance form fields
  const [showAddForm, setShowAddForm] = useState(false);
  const [newName, setNewName] = useState('');
  const [newUrl, setNewUrl] = useState('');
  const [newTimeout, setNewTimeout] = useState(30);

  // Load config & CDP models on mount
  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      setIsLoading(true);
      try {
        const [loadedConfig, loadedCdpModels] = await Promise.allSettled([
          api.getConfig(),
          api.getCdpModels(),
        ]);

        if (!isMounted) return;

        if (loadedConfig.status === 'fulfilled') {
          setConfig(loadedConfig.value);
        } else {
          setConfig(DEFAULT_CONFIG);
        }

        if (loadedCdpModels.status === 'fulfilled' && loadedCdpModels.value.length > 0) {
          setCdpModels(loadedCdpModels.value);
        } else {
          setCdpModels([
            'Gemini 4 Argon (Low)',
            'Gemini 4 Argon (Medium)',
            'Gemini 2.5 Pro',
            'Gemini 2.5 Flash',
          ]);
        }
      } catch (err) {
        if (isMounted) setConfig(DEFAULT_CONFIG);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Probe an Ollama instance and populate available models
  const handleTestInstance = useCallback(async (inst: OllamaInstance) => {
    setTestingId(inst.id);
    try {
      const res = await api.testOllamaInstance(inst);
      setTestResults((prev) => ({
        ...prev,
        [inst.id]: res,
      }));
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.detail : 'Connessione fallita';
      setTestResults((prev) => ({
        ...prev,
        [inst.id]: {
          online_status: false,
          latency_ms: 0,
          models_list: [],
          error: msg,
        },
      }));
    } finally {
      setTestingId(null);
    }
  }, []);

  // Add a new Ollama instance to config
  const handleAddInstance = () => {
    if (!config || !newName.trim() || !newUrl.trim()) return;
    const nextId = config.ollama_instances.length > 0
      ? Math.max(...config.ollama_instances.map((i) => i.id)) + 1
      : 1;

    const newInst: OllamaInstance = {
      id: nextId,
      name: newName.trim(),
      url: newUrl.trim(),
      enabled: true,
      timeout_sec: Number(newTimeout) || 30,
    };

    setConfig({
      ...config,
      ollama_instances: [...config.ollama_instances, newInst],
    });

    setNewName('');
    setNewUrl('');
    setNewTimeout(30);
    setShowAddForm(false);
  };

  // Remove an instance
  const handleRemoveInstance = (id: number) => {
    if (!config) return;
    if (config.ollama_instances.length <= 1) {
      alert('Almeno un\'istanza Ollama deve rimanere configurata.');
      return;
    }
    setConfig({
      ...config,
      ollama_instances: config.ollama_instances.filter((i) => i.id !== id),
    });
  };

  // Toggle instance enabled state
  const handleToggleInstance = (id: number) => {
    if (!config) return;
    setConfig({
      ...config,
      ollama_instances: config.ollama_instances.map((inst) =>
        inst.id === id ? { ...inst, enabled: !inst.enabled } : inst
      ),
    });
  };

  // Save current config
  const handleSave = async () => {
    if (!config) return;
    setIsSaving(true);
    setSaveStatus(null);
    try {
      const saved = await api.updateConfig(config);
      setConfig(saved);
      if (onSaveConfig) {
        onSaveConfig(saved);
      }
      setSaveStatus({ success: true, message: 'Configurazione salvata con successo!' });
      setTimeout(() => setSaveStatus(null), 4000);
    } catch (err: unknown) {
      const msg = err instanceof ApiError ? err.detail : 'Errore nel salvataggio della configurazione.';
      setSaveStatus({ success: false, message: msg });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading || !config) {
    return (
      <div className="max-w-4xl mx-auto p-6 text-zinc-400 flex items-center gap-2">
        <RefreshCw className="w-4 h-4 animate-spin text-zinc-500" />
        <span>Caricamento configurazione Jules Hub...</span>
      </div>
    );
  }

  // Determine current models list available for Junior model dropdown
  const selectedJuniorInstanceId = config.junior_config.instance_id;
  const juniorInstanceResult = testResults[selectedJuniorInstanceId];
  const detectedJuniorModels = juniorInstanceResult?.models_list ?? [];

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8 text-zinc-200">
      {/* Top Header & Save Button */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-zinc-100 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-indigo-400" />
            <span>Configurazione Hub &amp; Matrice Modelli</span>
          </h2>
          <p className="text-xs text-zinc-400 mt-0.5">
            Gestisci le istanze Ollama distribuite, gli slot di esecuzione Junior e il gate di revisione Senior.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {saveStatus ? (
            <span
              className={`text-xs px-2.5 py-1 rounded flex items-center gap-1.5 font-medium ${
                saveStatus.success
                  ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
                  : 'bg-rose-950/80 text-rose-300 border border-rose-800'
              }`}
            >
              {saveStatus.success ? (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
              )}
              {saveStatus.message}
            </span>
          ) : null}

          <button
            type="button"
            onClick={handleSave}
            disabled={isSaving}
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50"
          >
            {isSaving ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            <span>{isSaving ? 'Salvataggio...' : 'Salva Configurazione'}</span>
          </button>
        </div>
      </div>

      {/* Multi-Instance Ollama Registry */}
      <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-indigo-400" />
            <div>
              <h3 className="text-sm font-semibold text-zinc-100">
                Gestore Multi-Istanza Ollama
              </h3>
              <p className="text-xs text-zinc-400">
                Server Ollama registrati nel cluster locale o in rete per i task Junior e scan asincroni.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setShowAddForm(!showAddForm)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 transition-colors"
          >
            <Plus className="w-3.5 h-3.5 text-zinc-400" />
            <span>{showAddForm ? 'Annulla' : 'Aggiungi Istanza'}</span>
          </button>
        </div>

        {/* Add Instance Form */}
        {showAddForm ? (
          <div className="bg-zinc-950 border border-zinc-800 rounded-lg p-4 space-y-3">
            <h4 className="text-xs font-semibold text-zinc-200">Nuova Istanza Ollama</h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label htmlFor="inst-name" className="block text-[11px] text-zinc-400 mb-1">
                  Nome Istanza
                </label>
                <input
                  id="inst-name"
                  type="text"
                  placeholder="es. Node GPU 2"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-1.5 text-xs text-zinc-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label htmlFor="inst-url" className="block text-[11px] text-zinc-400 mb-1">
                  URL Endpoint
                </label>
                <input
                  id="inst-url"
                  type="text"
                  placeholder="http://192.168.1.100:11434"
                  value={newUrl}
                  onChange={(e) => setNewUrl(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-1.5 text-xs text-zinc-100 font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label htmlFor="inst-timeout" className="block text-[11px] text-zinc-400 mb-1">
                  Timeout (sec)
                </label>
                <input
                  id="inst-timeout"
                  type="number"
                  min={5}
                  max={120}
                  value={newTimeout}
                  onChange={(e) => setNewTimeout(Number(e.target.value))}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded px-3 py-1.5 text-xs text-zinc-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={handleAddInstance}
                disabled={!newName.trim() || !newUrl.trim()}
                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold transition-colors disabled:opacity-50"
              >
                Salva Nuova Istanza
              </button>
            </div>
          </div>
        ) : null}

        {/* Instances List */}
        <div className="space-y-3">
          {config.ollama_instances.map((inst) => {
            const probe = testResults[inst.id];
            const isTesting = testingId === inst.id;

            return (
              <div
                key={inst.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between bg-zinc-950 p-3.5 rounded-lg border border-zinc-800 gap-3"
              >
                <div className="flex items-start gap-3">
                  <input
                    type="checkbox"
                    id={`inst-toggle-${inst.id}`}
                    checked={inst.enabled}
                    onChange={() => handleToggleInstance(inst.id)}
                    className="mt-1 rounded bg-zinc-900 border-zinc-700 text-indigo-500 focus:ring-0 cursor-pointer"
                    title={inst.enabled ? 'Disabilita istanza' : 'Abilita istanza'}
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <label
                        htmlFor={`inst-toggle-${inst.id}`}
                        className={`text-sm font-semibold cursor-pointer ${
                          inst.enabled ? 'text-zinc-100' : 'text-zinc-500 line-through'
                        }`}
                      >
                        {inst.name}
                      </label>
                      <span className="text-[11px] font-mono text-zinc-500">#{inst.id}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
                        {inst.timeout_sec}s timeout
                      </span>
                    </div>
                    <div className="text-xs font-mono text-zinc-400 mt-0.5">{inst.url}</div>

                    {probe?.online_status && probe.models_list.length > 0 ? (
                      <div className="text-[11px] text-zinc-400 mt-1 flex items-center gap-1.5 flex-wrap">
                        <span className="text-zinc-500">Modelli rilevati ({probe.models_list.length}):</span>
                        {probe.models_list.slice(0, 4).map((m) => (
                          <span key={m} className="px-1.5 py-0.2 rounded bg-zinc-900 border border-zinc-800 text-zinc-300 font-mono text-[10px]">
                            {m}
                          </span>
                        ))}
                        {probe.models_list.length > 4 ? (
                          <span className="text-[10px] text-zinc-500">+{probe.models_list.length - 4} altri</span>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                </div>

                <div className="flex items-center gap-2.5 self-end sm:self-center">
                  {probe ? (
                    <span
                      className={`text-xs px-2.5 py-1 rounded flex items-center gap-1.5 font-medium ${
                        probe.online_status
                          ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
                          : 'bg-rose-950/80 text-rose-300 border border-rose-800'
                      }`}
                    >
                      {probe.online_status ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Online ({probe.latency_ms}ms)</span>
                        </>
                      ) : (
                        <>
                          <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
                          <span title={probe.error || ''}>Offline</span>
                        </>
                      )}
                    </span>
                  ) : null}

                  <button
                    type="button"
                    onClick={() => handleTestInstance(inst)}
                    disabled={isTesting}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded border border-zinc-700 transition-colors disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isTesting ? 'animate-spin' : ''}`} />
                    <span>{isTesting ? 'Verifica...' : 'Test & Carica Modelli'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleRemoveInstance(inst.id)}
                    className="p-1.5 text-zinc-500 hover:text-rose-400 hover:bg-zinc-800 rounded transition-colors"
                    title="Rimuovi istanza"
                    aria-label={`Rimuovi istanza ${inst.name}`}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Junior & Senior Slots Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Slot Junior Coder */}
        <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center gap-2 border-b border-zinc-800/80 pb-3">
            <Cpu className="w-5 h-5 text-amber-400" />
            <div>
              <h3 className="text-sm font-semibold text-zinc-100">Slot Junior Coder</h3>
              <p className="text-xs text-zinc-400">
                Esegue la generazione patch autonoma (&lt; 50 righe) e i test nel worktree isolato.
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {/* Provider choice */}
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">
                Provider Primario
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setConfig({
                      ...config,
                      junior_config: { ...config.junior_config, provider: 'ollama' },
                    })
                  }
                  className={`py-2 px-3 rounded text-xs font-semibold border transition-colors ${
                    config.junior_config.provider === 'ollama'
                      ? 'bg-zinc-800 text-zinc-100 border-zinc-600'
                      : 'bg-zinc-950 text-zinc-400 border-zinc-800 hover:text-zinc-200'
                  }`}
                >
                  Ollama (Locale / Rete)
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setConfig({
                      ...config,
                      junior_config: { ...config.junior_config, provider: 'antigravity_cli' },
                    })
                  }
                  className={`py-2 px-3 rounded text-xs font-semibold border transition-colors ${
                    config.junior_config.provider === 'antigravity_cli'
                      ? 'bg-zinc-800 text-zinc-100 border-zinc-600'
                      : 'bg-zinc-950 text-zinc-400 border-zinc-800 hover:text-zinc-200'
                  }`}
                >
                  Antigravity CLI (Flash)
                </button>
              </div>
            </div>

            {/* If Ollama: Select Instance */}
            {config.junior_config.provider === 'ollama' ? (
              <div>
                <label htmlFor="junior-instance" className="block text-xs font-medium text-zinc-300 mb-1">
                  Istanza Ollama
                </label>
                <select
                  id="junior-instance"
                  value={config.junior_config.instance_id}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      junior_config: {
                        ...config.junior_config,
                        instance_id: Number(e.target.value),
                      },
                    })
                  }
                  className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:border-zinc-700"
                >
                  {config.ollama_instances.map((inst) => (
                    <option key={inst.id} value={inst.id}>
                      {inst.name} ({inst.url}) {inst.enabled ? '' : '[Disabilitato]'}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}

            {/* Model Name selection */}
            <div>
              <label htmlFor="junior-model" className="block text-xs font-medium text-zinc-300 mb-1">
                Modello Junior
              </label>
              {detectedJuniorModels.length > 0 ? (
                <div className="space-y-1.5">
                  <select
                    id="junior-model"
                    value={config.junior_config.model_name}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        junior_config: {
                          ...config.junior_config,
                          model_name: e.target.value,
                        },
                      })
                    }
                    className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs text-zinc-100 focus:outline-none focus:border-zinc-700 font-mono"
                  >
                    {detectedJuniorModels.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                    {!detectedJuniorModels.includes(config.junior_config.model_name) ? (
                      <option value={config.junior_config.model_name}>
                        {config.junior_config.model_name} (personalizzato)
                      </option>
                    ) : null}
                  </select>
                </div>
              ) : (
                <input
                  id="junior-model"
                  type="text"
                  value={config.junior_config.model_name}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      junior_config: {
                        ...config.junior_config,
                        model_name: e.target.value,
                      },
                    })
                  }
                  placeholder="qwen2.5-coder o nome tag Ollama"
                  className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs text-zinc-100 font-mono focus:outline-none focus:border-zinc-700"
                />
              )}
            </div>

            {/* Fallback Configuration */}
            <div className="pt-2 border-t border-zinc-800/80 space-y-2">
              <span className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
                Configurazione Fallback Opzionale
              </span>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label htmlFor="fallback-provider" className="block text-[11px] text-zinc-400 mb-1">
                    Provider Fallback
                  </label>
                  <select
                    id="fallback-provider"
                    value={config.junior_config.fallback_provider || 'none'}
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        junior_config: {
                          ...config.junior_config,
                          fallback_provider: e.target.value === 'none' ? undefined : e.target.value,
                        },
                      })
                    }
                    className="w-full bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-zinc-100 focus:outline-none"
                  >
                    <option value="none">Nessun Fallback</option>
                    <option value="antigravity_cli">Antigravity CLI</option>
                    <option value="ollama">Ollama</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="fallback-model" className="block text-[11px] text-zinc-400 mb-1">
                    Modello Fallback
                  </label>
                  <input
                    id="fallback-model"
                    type="text"
                    value={config.junior_config.fallback_model || ''}
                    placeholder="flash"
                    onChange={(e) =>
                      setConfig({
                        ...config,
                        junior_config: {
                          ...config.junior_config,
                          fallback_model: e.target.value || undefined,
                        },
                      })
                    }
                    className="w-full bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-zinc-100 font-mono focus:outline-none"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Slot Senior Reviewer */}
        <section className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center gap-2 border-b border-zinc-800/80 pb-3">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <div>
              <h3 className="text-sm font-semibold text-zinc-100">Slot Senior Reviewer</h3>
              <p className="text-xs text-zinc-400">
                Audit gate prima della creazione Pull Request: verifica scope &lt; 50 righe, sicurezza e test.
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {/* Modalità Senior Review */}
            <div>
              <label className="block text-xs font-medium text-zinc-300 mb-1">
                Modalità di Revisione Senior
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setConfig({
                      ...config,
                      senior_mode: 'cdp',
                      senior_config: {
                        ...config.senior_config,
                        provider: 'cdp',
                        model_name: config.senior_config.model_name || 'Gemini 4 Argon (Low)',
                      },
                    })
                  }
                  className={`py-2 px-3 rounded text-xs font-semibold border transition-colors ${
                    config.senior_mode === 'cdp'
                      ? 'bg-zinc-800 text-zinc-100 border-zinc-600'
                      : 'bg-zinc-950 text-zinc-400 border-zinc-800 hover:text-zinc-200'
                  }`}
                >
                  Antigravity IDE via CDP :9000
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setConfig({
                      ...config,
                      senior_mode: 'in_cockpit',
                      senior_config: {
                        ...config.senior_config,
                        provider: 'ollama',
                      },
                    })
                  }
                  className={`py-2 px-3 rounded text-xs font-semibold border transition-colors ${
                    config.senior_mode === 'in_cockpit'
                      ? 'bg-zinc-800 text-zinc-100 border-zinc-600'
                      : 'bg-zinc-950 text-zinc-400 border-zinc-800 hover:text-zinc-200'
                  }`}
                >
                  In-Cockpit Senior Review
                </button>
              </div>
            </div>

            {/* Model Picker for Senior */}
            <div>
              <label htmlFor="senior-model-select" className="block text-xs font-medium text-zinc-300 mb-1">
                Modello Revisore Senior
              </label>
              <select
                id="senior-model-select"
                value={config.senior_config.model_name}
                onChange={(e) =>
                  setConfig({
                    ...config,
                    senior_config: {
                      ...config.senior_config,
                      model_name: e.target.value,
                    },
                  })
                }
                className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-xs text-zinc-100 font-mono focus:outline-none focus:border-zinc-700"
              >
                {/* CDP Models or Fallback Models */}
                {cdpModels.map((m) => (
                  <option key={m} value={m}>
                    {m} {m.includes('Argon (Low)') ? '★ (Prima scelta consigliata)' : ''}
                  </option>
                ))}
                {!cdpModels.includes(config.senior_config.model_name) ? (
                  <option value={config.senior_config.model_name}>
                    {config.senior_config.model_name}
                  </option>
                ) : null}
              </select>
              <p className="text-[11px] text-zinc-500 mt-1">
                {config.senior_mode === 'cdp'
                  ? 'Il modello viene selezionato automaticamente nel selettore Antigravity via porta 9000.'
                  : 'Il prompt di audit viene inviato all\'engine locale/Ollama configurato.'}
              </p>
            </div>

            {/* Scope Ceiling & CDP Port Settings */}
            <div className="pt-2 border-t border-zinc-800/80 grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="max-diff-lines" className="block text-[11px] text-zinc-400 mb-1">
                  Scope Ceiling (Max Righe Diff)
                </label>
                <input
                  id="max-diff-lines"
                  type="number"
                  min={10}
                  max={200}
                  value={config.max_diff_lines}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      max_diff_lines: Number(e.target.value) || 50,
                    })
                  }
                  className="w-full bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-zinc-100 font-mono focus:outline-none"
                />
              </div>

              <div>
                <label htmlFor="cdp-port" className="block text-[11px] text-zinc-400 mb-1">
                  Porta CDP Debugger
                </label>
                <input
                  id="cdp-port"
                  type="number"
                  value={config.cdp_port}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      cdp_port: Number(e.target.value) || 9000,
                    })
                  }
                  className="w-full bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-zinc-100 font-mono focus:outline-none"
                />
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};
