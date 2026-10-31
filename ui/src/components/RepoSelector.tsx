import React, { useState } from 'react';
import { FolderGit2, ChevronDown, Search, Check } from 'lucide-react';
import type { ProjectInfo } from '../types';

interface RepoSelectorProps {
  projects: ProjectInfo[];
  selectedRepo: string;
  onSelectRepo: (repoName: string) => void;
  isLoading?: boolean;
}

export const RepoSelector: React.FC<RepoSelectorProps> = ({
  projects,
  selectedRepo,
  onSelectRepo,
  isLoading = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredProjects = projects.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.description && p.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const currentProject = projects.find((p) => p.name === selectedRepo);

  return (
    <div className="relative">
      <div className="flex items-center gap-2">
        <label htmlFor="repo-select-button" className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
          Target Workspace:
        </label>
        <button
          id="repo-select-button"
          type="button"
          onClick={() => setIsOpen(!isOpen)}
          disabled={isLoading}
          className="flex items-center gap-2.5 px-3 py-1.5 rounded-md bg-zinc-900 border border-zinc-800 text-zinc-100 hover:border-zinc-700 hover:bg-zinc-800/80 transition-colors focus:outline-none focus:ring-1 focus:ring-zinc-600 disabled:opacity-50"
          aria-haspopup="listbox"
          aria-expanded={isOpen}
        >
          <FolderGit2 className="w-4 h-4 text-zinc-400" />
          <span className="font-medium text-sm">
            {selectedRepo ? selectedRepo : 'Tutti i workspace (All)'}
          </span>
          <ChevronDown className={`w-3.5 h-3.5 text-zinc-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {projects.length > 0 && (
          <span className="text-xs text-zinc-500 ml-1">
            ({projects.length} repository registrati)
          </span>
        )}
      </div>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-20"
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute left-0 mt-2 w-80 max-h-96 z-30 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl overflow-hidden flex flex-col">
            {/* Search Input */}
            <div className="p-2 border-b border-zinc-800 bg-zinc-950/50">
              <div className="relative flex items-center">
                <Search className="w-4 h-4 text-zinc-400 absolute left-2.5 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Filtra workspace..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-zinc-900 text-sm text-zinc-100 placeholder-zinc-500 rounded pl-8 pr-3 py-1.5 border border-zinc-800 focus:outline-none focus:border-zinc-600"
                  autoFocus
                />
              </div>
            </div>

            {/* Repos list */}
            <div className="overflow-y-auto divide-y divide-zinc-800/50">
              {/* All Option */}
              <button
                type="button"
                onClick={() => {
                  onSelectRepo('');
                  setIsOpen(false);
                }}
                className={`w-full text-left px-3 py-2 text-sm flex items-center justify-between hover:bg-zinc-800/60 transition-colors ${
                  selectedRepo === '' ? 'bg-zinc-800/90 text-zinc-100 font-semibold' : 'text-zinc-300'
                }`}
              >
                <div>
                  <div className="font-medium">Tutti i workspace</div>
                  <div className="text-xs text-zinc-500">Scansione globale su tutti i repository</div>
                </div>
                {selectedRepo === '' && <Check className="w-4 h-4 text-zinc-300" />}
              </button>

              {filteredProjects.map((proj) => {
                const isSelected = selectedRepo === proj.name;
                return (
                  <button
                    key={proj.name}
                    type="button"
                    onClick={() => {
                      onSelectRepo(proj.name);
                      setIsOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 text-sm flex items-center justify-between hover:bg-zinc-800/60 transition-colors ${
                      isSelected ? 'bg-zinc-800/90 text-zinc-100 font-semibold' : 'text-zinc-300'
                    }`}
                  >
                    <div className="truncate pr-2">
                      <div className="font-medium truncate">{proj.name}</div>
                      <div className="text-xs text-zinc-500 truncate">{proj.path}</div>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-zinc-300 flex-shrink-0" />}
                  </button>
                );
              })}

              {filteredProjects.length === 0 && (
                <div className="p-4 text-center text-xs text-zinc-500">
                  Nessun repository trovato con il nome "{searchQuery}"
                </div>
              )}
            </div>

            {/* Quick footer with current path */}
            {currentProject && (
              <div className="p-2 bg-zinc-950/80 border-t border-zinc-800 text-[11px] text-zinc-500 truncate">
                Percorso: {currentProject.path}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
