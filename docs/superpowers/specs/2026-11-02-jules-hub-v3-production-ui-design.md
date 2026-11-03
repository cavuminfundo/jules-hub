# Specifiche Tecniche di Jules Hub v3 (Zero Mock, Community-Ready, Jules Official UI)

## 1. Rimozione Completa di `curator.py` e Migrazione dei Test CLI

- **Rimozione di `curator.py`:** Il modulo `curator.py` legacy verrà completamente rimosso dal codice base.
- **Migrazione dei Test CLI:** Tutti i test presenti nel modulo `curator.py` verranno migrati al nuovo framework di test CLI, assicurando la stessa copertura e qualità dei test.

## 2. Zero Hardcoding & Impostazioni Comunità

- **GitHub Token:** Il token di accesso GitHub sarà configurabile tramite variabili d'ambiente.
- **Cloud API Keys:** Le chiavi API per i servizi cloud saranno gestite tramite variabili d'ambiente.
- **Dynamic Ollama Registry:** Il registro Ollama sarà configurabile dinamicamente tramite variabili d'ambiente.
- **Git Commit Authoring:** Le impostazioni di autore per i commit Git saranno configurabili tramite variabili d'ambiente.
- **PR Export Settings:** Le impostazioni di esportazione delle Pull Request (PR) saranno configurabili tramite variabili d'ambiente.
- **Configurabili Percorsi tramite Env Vars:** Tutti i percorsi di configurazione saranno gestibili tramite variabili d'ambiente.

## 3. Zero Mock Production Backend

- **Real Git Diff Extraction from Worktree:** L'estrazione delle differenze Git dal worktree sarà effettuata in modo reale, senza mock.
- **Real AI Senior Review via Ollama/Cloud/CDP:** La revisione senior AI sarà effettuata tramite Ollama, Cloud o CDP, senza mock.
- **Real PR Creation via `gh pr create` / GitHub REST API:** La creazione delle Pull Request sarà effettuata tramite il comando `gh pr create` o l'API REST di GitHub, senza mock.
- **Real Free-form Prompt Execution and AI-assisted Scanner:** L'esecuzione di prompt free-form e lo scanner assistito da AI saranno effettuati in modo reale, senza mock.
- **Persistent Session History:** La cronologia delle sessioni sarà mantenuta in modo persistente.

## 4. Layout dell'UI Officiale di Jules

### Sidebar Sinistra (Collassabile)
- **Recent Sessions:** Elenco delle sessioni recenti.
- **Codebases:** Elenco dei codebases.

### Centro (Card Minimale)
- **Repo Dropdown:** Menu a discesa per selezionare il repository.

### Input Box per Prompt Free-form
- **Free-form Prompt Input Box:** Casella di input per inserire prompt free-form.

### 3 Tabs
- **Codebase Overview:** Panoramica del codebase.
- **Suggested Compact List Rows:** Lista compatta di suggerimenti con pulsante di avvio e pill di categoria.
- **Scheduled Skill-based Agents:** Agenti basati su skill pianificati.
- **Settings View:** Vista delle impostazioni con 4 sezioni:
  - **General:** Impostazioni generali.
  - **Integrations:** Integrazioni.
  - **MCP:** MCP (Management and Control Platform).
  - **API Key:** Gestione delle chiavi API.