# Specifiche Tecniche di Jules Hub v2 - Autonomia del Cockpit

## Visione & Obiettivo Architetturale

L'obiettivo di Jules Hub v2 è l'evoluzione da una piattaforma di test fumigene statica a una piattaforma autonoma e pronta per la community, ispirata a Google Jules. La separazione netta tra il **Ruolo Junior Coder** (responsabile della scansione, gestione del worktree, applicazione di micro-patch di meno di 50 righe e esecuzione dei test) e il **Ruolo Senior Reviewer / Tech Lead** (responsabile dell'audit di sicurezza, spiegazione chiara dei miglioramenti e del perché, e del gate obbligatorio prima di qualsiasi Pull Request) è fondamentale per garantire la qualità e la sicurezza del codice.

## Multi-Instance Ollama Registry & Auto-Discovery

### Supporto per N istanze Ollama configurabili in `hub_config.json`

- **Campi di configurazione:**
  - `id`: Identificatore univoco dell'istanza.
  - `name`: Nome descrittivo dell'istanza.
  - `url`: URL dell'istanza Ollama.
  - `enabled`: Flag per abilitare/disabilitare l'istanza.
  - `timeout_sec`: Timeout in secondi per le richieste all'istanza.

- **Esempi reali:**
  - GPU Server 24/7: `http://192.168.88.117:11434`
  - Workstation RTX 5070 Ti: `http://100.102.204.70:11434`

### Endpoints

- **GET /api/ollama/instances/{id}/models**: Restituisce lo stato online/offline, la latenza in ms e l'elenco dei modelli installati per l'istanza specificata.
- **POST /api/ollama/test**: Interroga `GET {url}/api/tags` per verificare lo stato dell'istanza e restituire le informazioni richieste.

## Matrice Universale Ruolo x Provider (Slot Junior & Slot Senior)

### Slot Junior Coder

- **Configurazione:**
  - `provider`: Ollama o antigravity_cli.
  - `instance_id`: Identificatore dell'istanza Ollama.
  - `model_name`: Nome del modello da utilizzare.
  - `fallback`: Configurazione opzionale per un fallback nel caso in cui la workstation primaria sia offline (inclusi `fallback_provider`, `fallback_instance_id`, `fallback_model`).

### Slot Senior Reviewer (Dual-Mode)

#### a) Modalità In-Cockpit Senior Review (Ollama Senior o Antigravity CLI)

- **Endpoint POST /api/tasks/{task_id}/senior-review**: Invia il diff e lo stato del worktree al modello Senior scelto.
- **Risposta SeniorReviewResult:**
  - `verdict`: APPROVED / REJECTED.
  - `simple_explanation`: Spiegazione chiara per l'utente.
  - `security_notes`: Note di sicurezza.
  - Se `verdict` è APPROVED, sblocca l'endpoint POST /api/tasks/{task_id}/create-pr per eseguire `git push` del branch worktree e creare una Pull Request.

#### b) Modalità Antigravity IDE Handoff via CDP (:9000)

- **Endpoint GET /api/cdp/models**: Legge via WebSocket CDP l'elenco dei modelli disponibili nel Model Picker.
- **Handoff:**
  - Quando l'utente invia al Senior via CDP (POST /api/escalate), il bridge CDP seleziona automaticamente nel DOM di Antigravity il modello Senior configurato e inietta il prompt strutturato per la verifica del worktree.

## AI Deep Scanner & Storico Proposte (hub/scanner.py)

### Funzionalità

- **Scansione AI-driven:**
  - Oltre alle euristiche AST/statiche, la scansione seleziona i file del repository (escludendo i suggerimenti già scartati o applicati salvati in `data/hub_state.json`).
  - Consulta i diari `journal/{bolt,palette,sentinel}.md` e usa il modello Junior configurato per individuare micro-miglioramenti contestuali (<50 righe) con motivazione chiara.

- **Endpoint POST /api/suggestions/{id}/discard**: Scarta un suggerimento e salva la sua firma in `ignored_suggestions` per evitare la riproposizione.

## Background Scheduler per Repository (hub/scheduler.py)

### Funzionalità

- **Loop asyncio integrato nel lifespan di FastAPI:**
  - Verifica ogni 60 secondi le configurazioni per-repository (in `data/hub_config.json`).

- **Campi per ogni repository:**
  - `repo_name`: Nome del repository.
  - `enabled`: Flag per abilitare/disabilitare il repository.
  - `interval_hours`: Intervallo di esecuzione (6, 12, 24 ore).
  - `personas`: Lista di persone (bolt, palette, sentinel).
  - `max_pending_worktrees`: Massimo numero di worktree pendenti (default 3).
  - `last_run_at`: Timestamp dell'ultima esecuzione.
  - `next_run_at`: Timestamp della prossima esecuzione.

- **Logica di scheduling:**
  - Se i worktree pendenti per quel repo sono < `max_pending_worktrees`, lo scheduler avvia in background la scansione AI Junior, crea il worktree isolato, applica la patch, esegue la test suite nel worktree e ferma il task in stato READY_FOR_SENIOR (o NEEDS_SENIOR_FIX), trasmettendo gli eventi via SSE (/api/events).

## Architettura File, Persistenza JSON & Contratti API REST

### Persistenza

- **File JSON:**
  - `/home/federico/jules/data/hub_config.json`: Configurazioni globali.
  - `/home/federico/jules/data/hub_state.json`: Stato attuale del sistema.

### Nuovi moduli backend

- `hub/config_store.py`
- `hub/scheduler.py`
- `hub/cdp_bridge.py`
- `hub/engine_router.py`
- `hub/scanner.py`
- `hub/app.py`

### Componenti React UI

- `ui/src/components/SettingsModal.tsx` o tab dedicata
- `SchedulerPanel.tsx`
- `SeniorReviewPanel.tsx` nel `DiffDrawer`

## Sicurezza & Guardrail

- **Zero PR automatiche senza approvazione Senior + click utente.**
- **Zero comandi shell=True, esecuzione esclusiva via list[str].**
- **Zero dirty working tree sui repository principali.**

---

Questo documento fornisce una specifica dettagliata e produttiva per l'architettura di Jules Hub v2, enfatizzando la separazione dei ruoli, l'auto-discovery delle istanze Ollama, la matrice dei ruoli e dei provider, la scansione AI-driven, il scheduling in background, la persistenza dei dati e le misure di sicurezza.