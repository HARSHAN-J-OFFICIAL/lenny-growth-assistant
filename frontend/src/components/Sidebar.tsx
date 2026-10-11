import React, { useState } from "react";
import {
  MessageSquare,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  ChevronLeft,
  ChevronRight,
  Database,
  Cpu,
  Layers,
} from "lucide-react";
import type { Session } from "../types";
import { SignalLogo } from "./SignalLogo";

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  onRenameSession: (id: string, newTitle: string) => Promise<void>;
  onDeleteSession: (id: string) => Promise<void>;
  isOpen: boolean;
  onToggleOpen: () => void;
  currentProvider?: string;
  currentModel?: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onRenameSession,
  onDeleteSession,
  isOpen,
  onToggleOpen,
  currentProvider = "ollama",
  currentModel = "llama3.2",
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const startEditing = (s: Session, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(s.id);
    setEditTitle(s.title);
  };

  const handleSaveRename = async (id: string, e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!editTitle.trim()) return;
    try {
      await onRenameSession(id, editTitle.trim());
      setEditingId(null);
    } catch (err) {
      console.error("Failed to rename session:", err);
    }
  };

  const handleConfirmDelete = async (id: string) => {
    setIsDeleting(true);
    try {
      await onDeleteSession(id);
      setDeletingId(null);
    } finally {
      setIsDeleting(false);
    }
  };

  if (!isOpen) {
    return (
      <div className="w-16 h-full bg-[#172634] border-r border-white/5 flex flex-col items-center py-4 justify-between select-none shrink-0 z-30 transition-all duration-200">
        <div className="flex flex-col items-center gap-4">
          <button
            onClick={onToggleOpen}
            className="p-2 rounded-xl bg-[#233645]/80 hover:bg-[#233645] text-[#FFF6E9] transition shadow-sm"
            title="Expand Research Library"
            aria-label="Expand Research Library"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          <SignalLogo size="sm" showWordmark={false} showSubtitle={false} />
          <button
            onClick={onNewSession}
            className="p-2.5 rounded-xl bg-[#FF7952] hover:bg-[#FF6436] text-[#101B27] shadow-coral-glow hover:scale-105 active:scale-95 transition"
            title="New Conversation"
            aria-label="New Conversation"
          >
            <Plus className="w-4 h-4 font-bold" />
          </button>
        </div>
        <div className="flex flex-col items-center gap-2 text-[#687782]">
          <span className="w-2 h-2 rounded-full bg-[#75D2BB]" title="System Operational" />
        </div>
      </div>
    );
  }

  return (
    <aside className="w-72 h-full bg-[#172634] border-r border-white/5 flex flex-col justify-between select-none shrink-0 z-30 transition-all duration-200 text-[#FFF6E9]">
      {/* Top Header & Branding */}
      <div className="p-4 border-b border-white/5 bg-[#172634]/95">
        <div className="flex items-center justify-between mb-4">
          <SignalLogo size="md" showWordmark={true} showSubtitle={true} />
          <button
            onClick={onToggleOpen}
            className="p-1.5 rounded-lg text-[#687782] hover:text-[#FFF6E9] hover:bg-[#233645] transition"
            title="Collapse Sidebar"
            aria-label="Collapse Sidebar"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
        </div>

        {/* Primary Action Button: Signal Coral */}
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-[#FF7952] hover:bg-[#FF6436] active:scale-[0.98] text-[#101B27] font-sans font-semibold text-xs shadow-coral-glow transition-all duration-150 group"
          aria-label="Start new research conversation"
        >
          <Plus className="w-4 h-4 text-[#101B27] stroke-[2.5]" />
          <span>New conversation</span>
          <span className="ml-auto text-[10px] font-mono px-1.5 py-0.5 rounded bg-black/15 text-[#101B27]/80 font-medium">
            Ctrl+K
          </span>
        </button>
      </div>

      {/* Persistent Conversation List (Editorial Research Notebook) */}
      <div className="flex-1 overflow-y-auto px-2 py-3 space-y-1">
        <div className="px-3 pb-2 text-[10px] font-mono tracking-widest uppercase text-[#687782] flex items-center justify-between">
          <span>RESEARCH SESSIONS</span>
          <span className="px-1.5 py-0.2 rounded bg-white/5 text-[#FFF6E9]/60">{sessions.length}</span>
        </div>

        {sessions.length === 0 ? (
          <div className="px-3 py-10 text-center text-xs text-[#687782] space-y-2">
            <Layers className="w-6 h-6 mx-auto opacity-40 text-[#75D2BB]" />
            <p>No research sessions yet.</p>
            <p className="text-[11px] text-[#687782]/80">
              Start a new session to query 303 podcast episodes.
            </p>
          </div>
        ) : (
          sessions.map((session) => {
            const isActive = session.id === activeSessionId;
            const isEditing = editingId === session.id;

            return (
              <div
                key={session.id}
                onClick={() => !isEditing && onSelectSession(session.id)}
                className={`group relative flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-xs transition-all duration-150 cursor-pointer ${
                  isActive
                    ? "bg-[#233645] text-[#FFF6E9] shadow-sm"
                    : "text-[#D7E1D8]/80 hover:text-[#FFF6E9] hover:bg-[#233645]/50"
                }`}
              >
                {/* Active Indicator: Distinctive Thin Signal Coral Bar */}
                {isActive && (
                  <div className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-[#FF7952]" />
                )}

                <MessageSquare
                  className={`w-3.5 h-3.5 shrink-0 ${
                    isActive ? "text-[#FF7952]" : "text-[#687782] group-hover:text-[#D7E1D8]"
                  }`}
                />

                {isEditing ? (
                  <form
                    onSubmit={(e) => handleSaveRename(session.id, e)}
                    className="flex-1 flex items-center gap-1"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="w-full bg-[#101B27] border border-[#FF7952] rounded-lg px-2 py-0.5 text-xs text-[#FFF6E9] focus:outline-none"
                      autoFocus
                    />
                    <button
                      type="submit"
                      className="p-1 text-[#75D2BB] hover:text-[#99ECD8]"
                      title="Save"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingId(null)}
                      className="p-1 text-[#687782] hover:text-[#FFF6E9]"
                      title="Cancel"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </form>
                ) : (
                  <>
                    <span className="truncate flex-1 font-sans text-xs">
                      {session.title}
                    </span>

                    {/* Action buttons: visible on active session or on hover */}
                    <div
                      className={`flex items-center gap-0.5 shrink-0 ${
                        isActive
                          ? "opacity-90 hover:opacity-100"
                          : "opacity-0 group-hover:opacity-100 transition-opacity"
                      }`}
                    >
                      <button
                        onClick={(e) => startEditing(session, e)}
                        className="p-1 text-[#687782] hover:text-[#FFF6E9] transition rounded hover:bg-white/10"
                        title="Rename conversation"
                        aria-label="Rename conversation"
                      >
                        <Edit2 className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeletingId(session.id);
                        }}
                        className="p-1 text-[#687782] hover:text-rose-400 transition rounded hover:bg-white/10"
                        title="Delete conversation"
                        aria-label="Delete conversation"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deletingId && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#172634] border border-white/10 rounded-2xl p-6 max-w-sm w-full shadow-2xl space-y-4">
            <h3 className="font-serif text-base text-[#FFF6E9]">Delete Research Session?</h3>
            <p className="text-xs text-[#D7E1D8]/80 leading-relaxed">
              This will permanently remove this session, including citations and generated artifacts, from the local PostgreSQL store.
            </p>
            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                disabled={isDeleting}
                onClick={() => setDeletingId(null)}
                className="px-3 py-1.5 rounded-lg text-xs text-[#D7E1D8] hover:bg-white/5 transition"
              >
                Cancel
              </button>
              <button
                disabled={isDeleting}
                onClick={() => handleConfirmDelete(deletingId)}
                className="px-3.5 py-1.5 rounded-lg text-xs bg-rose-600 hover:bg-rose-500 text-white font-medium transition"
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sidebar Footer: Operational Context */}
      <div className="p-3.5 border-t border-white/5 bg-[#101B27]/60 text-[11px] space-y-2">
        <div className="flex items-center justify-between text-[#D7E1D8]/70">
          <span className="flex items-center gap-1.5">
            <Database className="w-3 h-3 text-[#75D2BB]" />
            303 Episodes
          </span>
          <span className="font-mono text-[10px] text-[#687782]">32,209 chunks</span>
        </div>
        <div className="flex items-center justify-between text-[#D7E1D8]/70">
          <span className="flex items-center gap-1.5">
            <Cpu className="w-3 h-3 text-[#FF7952]" />
            <span className="truncate max-w-[120px] font-mono text-[10px]">
              {currentProvider}: {currentModel}
            </span>
          </span>
          <span className="flex items-center gap-1 text-[#75D2BB] font-mono text-[10px]">
            <span className="w-1.5 h-1.5 rounded-full bg-[#75D2BB] animate-pulse" />
            Active
          </span>
        </div>
      </div>
    </aside>
  );
};
