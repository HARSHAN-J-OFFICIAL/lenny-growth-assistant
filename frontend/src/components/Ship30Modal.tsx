import React, { useState, useEffect, useRef } from "react";
import { X, Loader2, AlertCircle } from "lucide-react";

interface Ship30ModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (topic: string, targetAudience: string) => Promise<void>;
  isLoading: boolean;
  errorMessage?: string | null;
  onClearError?: () => void;
}

/**
 * Editorial Writing Brief: Ship 30 for 30 Essay Generator
 * Centered floating modal with backdrop blur, keyboard escape handling,
 * warm paper form surfaces, and Signal Coral action.
 */
export const Ship30Modal: React.FC<Ship30ModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading,
  errorMessage,
  onClearError,
}) => {
  const [topic, setTopic] = useState("");
  const [targetAudience, setTargetAudience] = useState("Product Managers & Early Founders");
  const modalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input and handle Escape key
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape" && !isLoading) {
          onClose();
        }
      };
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [isOpen, isLoading, onClose]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim() || isLoading) return;
    if (onClearError) onClearError();
    await onSubmit(topic.trim(), targetAudience.trim());
  };

  const sampleTopics = [
    "Product-Led Growth Loops according to Elena Verna",
    "Founder Mode vs Manager Mode by Brian Chesky",
    "How High-Agency Product Leaders Think by Shreyas Doshi",
    "Finding Product-Market Fit in B2B SaaS",
  ];

  return (
    <div
      className="fixed inset-0 bg-[#101B27]/80 backdrop-blur-md z-50 flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isLoading) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="ship30-modal-title"
    >
      <div
        ref={modalRef}
        className="bg-[#172634] text-[#FFF6E9] border border-white/10 rounded-3xl p-6 sm:p-8 max-w-xl w-full shadow-2xl space-y-6 relative animate-in zoom-in-95 duration-150 my-auto"
      >
        {/* Top Header: Editorial Writing Brief */}
        <div className="flex items-start justify-between gap-4 border-b border-white/8 pb-5">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[10px] tracking-widest uppercase px-2 py-0.5 rounded-full bg-[#FF7952]/15 text-[#FF7952] border border-[#FF7952]/30">
                EDITORIAL BRIEF
              </span>
              <span className="font-mono text-[10px] text-[#75D2BB]">
                Ship 30 for 30 Method
              </span>
            </div>
            <h2 id="ship30-modal-title" className="font-serif text-2xl text-[#FFF6E9] font-normal leading-tight">
              Make something worth reading.
            </h2>
            <p className="text-xs text-[#D7E1D8]/80 font-sans leading-relaxed">
              Turn the best ideas from Lenny's conversations into a compelling Ship 30 essay.
            </p>
          </div>

          <button
            onClick={onClose}
            disabled={isLoading}
            className="p-2 rounded-xl text-[#687782] hover:text-[#FFF6E9] hover:bg-white/5 transition disabled:opacity-50"
            title="Close modal (Esc)"
            aria-label="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Actionable Error Banner */}
        {errorMessage && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-start gap-3 animate-in fade-in">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <div className="font-semibold text-rose-200">Essay Generation Notice</div>
              <div className="leading-relaxed text-rose-300/90">{errorMessage}</div>
              <div className="text-[11px] text-rose-400/80 pt-0.5">
                Your topic has been preserved. Check that the backend is active, then click below to retry.
              </div>
            </div>
          </div>
        )}

        {/* Truthful Loading State */}
        {isLoading && (
          <div className="p-4 rounded-2xl bg-[#FF7952]/10 border border-[#FF7952]/30 text-[#FFF6E9] text-xs flex items-center gap-3.5 animate-in fade-in">
            <Loader2 className="w-5 h-5 animate-spin text-[#FF7952] shrink-0" />
            <div className="leading-snug space-y-0.5">
              <div className="font-medium text-[#FFF6E9]">Developing your essay...</div>
              <div className="text-[11px] text-[#D7E1D8]/80">
                Searching 303 episodes, formatting 1-3-1 cadence & persisting artifact (~20-30s)
              </div>
            </div>
          </div>
        )}

        {/* Writing Form */}
        <form onSubmit={handleSubmit} className="space-y-4.5">
          {/* Topic Input */}
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-[#D7E1D8]">
              Essay Topic or Core Question
            </label>
            <input
              ref={inputRef}
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="e.g. Elena Verna on Product-Led Growth loops"
              disabled={isLoading}
              className="w-full bg-[#FFF9F0] text-[#142331] placeholder-[#687782] border border-white/10 rounded-xl px-4 py-2.5 text-xs font-sans focus:outline-none focus:ring-2 focus:ring-[#FF7952] disabled:opacity-50 transition shadow-sm"
              required
            />
          </div>

          {/* Quick Idea Starters */}
          <div className="space-y-2">
            <span className="block text-[10px] font-mono tracking-wider uppercase text-[#687782]">
              OR SELECT AN EDITORIAL HOOK:
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {sampleTopics.map((sample) => (
                <button
                  key={sample}
                  type="button"
                  onClick={() => setTopic(sample)}
                  disabled={isLoading}
                  className="group min-h-[58px] w-full p-3 rounded-xl bg-[#233645]/70 hover:bg-[#233645] border border-white/8 hover:border-[#FF7952]/40 text-left transition-all duration-150 disabled:opacity-50 flex items-center focus:outline-none focus:ring-1 focus:ring-[#FF7952]/50 cursor-pointer"
                >
                  <span className="block w-full text-[11.5px] leading-snug text-[#D7E1D8] group-hover:text-[#FFF6E9] font-medium line-clamp-2 transition-colors">
                    {sample}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Target Audience Input */}
          <div className="space-y-1.5 pt-1">
            <label className="block text-xs font-medium text-[#D7E1D8]">
              Target Audience
            </label>
            <input
              type="text"
              value={targetAudience}
              onChange={(e) => setTargetAudience(e.target.value)}
              placeholder="Product Managers & Early Founders"
              disabled={isLoading}
              className="w-full bg-[#FFF9F0] text-[#142331] placeholder-[#687782] border border-white/10 rounded-xl px-4 py-2.5 text-xs font-sans focus:outline-none focus:ring-2 focus:ring-[#FF7952] disabled:opacity-50 transition shadow-sm"
            />
          </div>

          {/* Modal Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-white/8">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl text-xs text-[#D7E1D8] hover:text-[#FFF6E9] hover:bg-white/5 transition disabled:opacity-50 font-medium"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={!topic.trim() || isLoading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#FF7952] hover:bg-[#FF6436] active:scale-95 disabled:opacity-40 disabled:hover:bg-[#FF7952] text-[#101B27] font-semibold text-xs transition-all shadow-coral-glow"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin stroke-[2.5]" />
                  <span>Generating essay...</span>
                </>
              ) : (
                <>
                  <span>Generate essay →</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
