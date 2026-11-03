import React, { useState } from 'react';
import {
  Search,
  ChevronDown,
  Clock,
  FolderGit2,
  X,
} from 'lucide-react';
import type { ProjectInfo, SessionRecord, TaskStatus } from '../types';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  sessions: SessionRecord[];
  projects: ProjectInfo[];
  selectedRepo: string;
  onSelectRepo: (repo: string) => void;
  onSelectSession: (session: SessionRecord) => void;
  activeTaskId?: string | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  sessions,
  projects,
  selectedRepo,
  onSelectRepo,
  onSelectSession,
  activeTaskId,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [recentSessionsOpen, setRecentSessionsOpen] = useState(true);
  const [codebasesOpen, setCodebasesOpen] = useState(true);

  const query = searchQuery.trim().toLowerCase();

  const filteredSessions = sessions.filter((s) => {
    if (!query) return true;
    const matchTitle = s.title?.toLowerCase().includes(query);
    const matchPrompt = s.prompt?.toLowerCase().includes(query);
    const matchRepo = s.repo?.toLowerCase().includes(query);
    return Boolean(matchTitle || matchPrompt || matchRepo);
  });

  const filteredProjects = projects.filter((p) => {
    if (!query) return true;
    const matchName = p.name.toLowerCase().includes(query);
    const matchDesc = p.description?.toLowerCase().includes(query);
    return Boolean(matchName || matchDesc);
  });

  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case 'passed':
      case 'completed':
        return 'bg-emerald-400';
      case 'failed':
        return 'bg-rose-400';
      case 'running':
      case 'testing':
        return 'bg-[#a78bfa] animate-pulse';
      case 'needs_escalation':
        return 'bg-amber-400';
      default:
        return 'bg-zinc-400';
    }
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-xs z-30 md:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar Panel */}
      <aside
        className={`fixed md:relative top-0 inset-y-0 left-0 z-40 md:z-10 bg-[#101014] border-r border-zinc-800/80 flex flex-col transition-all duration-200 ease-in-out shrink-0 select-none ${
          isOpen
            ? 'w-[260px] translate-x-0'
            : '-translate-x-full w-0 opacity-0 pointer-events-none border-r-0 overflow-hidden'
        }`}
        aria-label="Sidebar navigation"
      >
        <div className="w-[260px] flex flex-col h-full">
          {/* Top Header inside sidebar */}
          <div className="h-14 px-4 flex items-center justify-between border-b border-zinc-800/80">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-zinc-100 tracking-tight text-sm">
                julius
              </span>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                v3
              </span>
            </div>
            <button
              type="button"
              onClick={onClose}
              aria-label="Close sidebar"
              className="md:hidden p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Search Input Box */}
          <div className="p-3">
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for repo or sessions"
                className="w-full bg-[#16161d] border border-zinc-800 text-zinc-100 placeholder-zinc-400 text-xs rounded-lg py-2 pl-8 pr-3 focus:outline-none focus:border-[#8b5cf6] transition-colors"
              />
            </div>
          </div>

          {/* Scrollable Navigation Sections */}
          <div className="flex-1 overflow-y-auto px-2 space-y-4">
            {/* Section: Recent sessions */}
            <div>
              <button
                type="button"
                onClick={() => setRecentSessionsOpen(!recentSessionsOpen)}
                className="w-full flex items-center justify-between px-2 py-1.5 text-xs font-semibold text-zinc-400 uppercase tracking-wider hover:text-zinc-200 transition-colors min-h-[36px]"
                aria-expanded={recentSessionsOpen}
              >
                <span>Recent sessions</span>
                <ChevronDown
                  className={`w-3.5 h-3.5 transition-transform ${
                    recentSessionsOpen ? '' : '-rotate-90'
                  }`}
                />
              </button>

              {recentSessionsOpen && (
                <div className="mt-1 space-y-0.5">
                  {filteredSessions.length === 0 ? (
                    <div className="py-8 px-3 text-center flex flex-col items-center justify-center rounded-lg border border-dashed border-zinc-800/80 bg-zinc-900/20">
                      <div className="w-9 h-9 rounded-full bg-zinc-800/80 flex items-center justify-center text-zinc-400 mb-2">
                        <Clock className="w-4 h-4" />
                      </div>
                      <p className="text-xs text-zinc-400 font-medium">
                        Recent sessions will show up here
                      </p>
                    </div>
                  ) : (
                    filteredSessions.map((session) => {
                      const isActive = session.task_id === activeTaskId;
                      return (
                        <button
                          key={session.task_id}
                          type="button"
                          onClick={() => {
                            onSelectSession(session);
                            if (window.innerWidth < 768) onClose();
                          }}
                          className={`w-full text-left px-2.5 py-2 rounded-lg transition-colors flex items-center gap-2.5 min-h-[44px] group ${
                            isActive
                              ? 'bg-[#2e2348] text-zinc-100 border border-[#8b5cf6]/40'
                              : 'hover:bg-zinc-800/50 text-zinc-300'
                          }`}
                        >
                          <span
                            className={`w-2 h-2 rounded-full shrink-0 ${getStatusColor(
                              session.status
                            )}`}
                          />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium text-zinc-200 truncate group-hover:text-white">
                              {session.title || session.prompt || 'Untitled session'}
                            </p>
                            <p className="text-[11px] text-zinc-400 truncate">
                              {session.repo}
                            </p>
                          </div>
                        </button>
                      );
                    })
                  )}
                </div>
              )}
            </div>

            {/* Section: Codebases */}
            <div>
              <button
                type="button"
                onClick={() => setCodebasesOpen(!codebasesOpen)}
                className="w-full flex items-center justify-between px-2 py-1.5 text-xs font-semibold text-zinc-400 uppercase tracking-wider hover:text-zinc-200 transition-colors min-h-[36px]"
                aria-expanded={codebasesOpen}
              >
                <span>Codebases</span>
                <ChevronDown
                  className={`w-3.5 h-3.5 transition-transform ${
                    codebasesOpen ? '' : '-rotate-90'
                  }`}
                />
              </button>

              {codebasesOpen && (
                <div className="mt-1 space-y-0.5">
                  {filteredProjects.length === 0 ? (
                    <div className="py-4 px-2 text-center text-xs text-zinc-400">
                      Nessun codebase trovato
                    </div>
                  ) : (
                    filteredProjects.map((p) => {
                      const isSelected = selectedRepo === p.name;
                      return (
                        <button
                          key={p.name}
                          type="button"
                          onClick={() => {
                            onSelectRepo(p.name);
                            if (window.innerWidth < 768) onClose();
                          }}
                          className={`w-full text-left px-2.5 py-2 rounded-lg transition-colors flex items-center gap-2.5 min-h-[44px] ${
                            isSelected
                              ? 'bg-zinc-800 text-zinc-100 font-medium'
                              : 'hover:bg-zinc-800/50 text-zinc-300'
                          }`}
                        >
                          <FolderGit2 className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
                          <span className="text-xs truncate flex-1">
                            {p.name}
                          </span>
                          {isSelected && (
                            <span className="w-1.5 h-1.5 rounded-full bg-[#8b5cf6]" />
                          )}
                        </button>
                      );
                    })
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Bottom user/community info */}
          <div className="p-3 border-t border-zinc-800/80">
            <div className="flex items-center justify-between text-[11px] text-zinc-400">
              <span className="truncate">Local Workspaces</span>
              <span className="font-mono text-zinc-400">
                {projects.length} repos
              </span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
