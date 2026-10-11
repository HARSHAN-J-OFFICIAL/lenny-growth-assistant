import React, { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Send,
  Cpu,
  ChevronDown,
  ChevronUp,
  FileText,
  Wrench,
  Zap,
  Radio,
  ArrowRight,
  Cloud,
  HardDrive,
  PenTool,
} from "lucide-react";
import type { Message, Session, ProvidersStatusResponse } from "../types";
import { CitationCard } from "./CitationCard";

interface ChatWorkspaceProps {
  session: Session | null;
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (text: string) => Promise<void>;
  selectedModelProvider: string;
  selectedModelName: string;
  onSelectModel: (provider: string, modelName: string) => void;
  agentSdk: string;
  onSelectAgentSdk: (sdk: string) => void;
  onOpenShip30: () => void;
  isArtifactOpen: boolean;
  onToggleArtifact: () => void;
  artifactCount: number;
  providersStatus?: ProvidersStatusResponse | null;
}

export const ChatWorkspace: React.FC<ChatWorkspaceProps> = ({
  session,
  messages,
  isLoading,
  onSendMessage,
  selectedModelProvider,
  selectedModelName,
  onSelectModel,
  agentSdk,
  onSelectAgentSdk,
  onOpenShip30,
  isArtifactOpen,
  onToggleArtifact,
  artifactCount,
  providersStatus,
}) => {
  const [inputText, setInputText] = useState("");
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const [expandedTraceIndex, setExpandedTraceIndex] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;
    const text = inputText.trim();
    setInputText("");
    await onSendMessage(text);
  };

  const promptStarters = [
    {
      title: "Find product-market fit",
      tagline: "Frameworks & signals",
      query: "What are the counterintuitive frameworks for finding and validating product-market fit according to Lenny's guests?",
    },
    {
      title: "Improve user retention",
      tagline: "Diagnose & fix churn",
      query: "According to retention experts like Casey Winters and Elena Verna, how do top companies diagnose and fix churn?",
    },
    {
      title: "Build a growth strategy",
      tagline: "Compounding growth loops",
      query: "How should an early-stage company construct compounding acquisition loops rather than relying on linear funnels?",
    },
    {
      title: "Learn from great product leaders",
      tagline: "High agency & craft",
      query: "What traits distinguish world-class product leaders from average ones, based on interviews with Brian Chesky, Shreyas Doshi, and Claire Vo?",
    },
  ];

  const isOpenAiConfigured = providersStatus?.providers.find((p) => p.id === "openai")?.is_configured ?? false;
  const isAnthropicConfigured = providersStatus?.providers.find((p) => p.id === "anthropic")?.is_configured ?? false;
  const isGroqConfigured = providersStatus?.providers.find((p) => p.id === "groq")?.is_configured ?? false;
  const groqProvider = providersStatus?.providers.find((p) => p.id === "groq");
  const groqDefaultModel = groqProvider?.default_model || "openai/gpt-oss-20b";

  const modelOptions = [
    // LOCAL MODELS
    {
      provider: "ollama",
      modelName: "llama3.2",
      label: "Ollama Llama 3.2 3B",
      type: "local",
      badge: "Connected",
      isConfigured: true,
      isLocal: true,
    },
    {
      provider: "ollama",
      modelName: "qwen2.5:1.5b",
      label: "Ollama Qwen 2.5 1.5B",
      type: "local",
      badge: "Ultra-Light",
      isConfigured: true,
      isLocal: true,
    },
    // CLOUD MODELS
    {
      provider: "groq",
      modelName: groqDefaultModel,
      label: "Groq Cloud (GPT-OSS 20B)",
      type: "cloud",
      badge: isGroqConfigured ? "Free Tier Live" : "Unconfigured",
      isConfigured: isGroqConfigured,
      isLocal: false,
    },
    {
      provider: "openai",
      modelName: "gpt-4o",
      label: "OpenAI GPT-4o",
      type: "cloud",
      badge: isOpenAiConfigured ? "Connected" : "Requires Key",
      isConfigured: isOpenAiConfigured,
      isLocal: false,
    },
    {
      provider: "anthropic",
      modelName: "claude-sonnet-4-6",
      label: "Anthropic Claude Sonnet 4.6",
      type: "cloud",
      badge: isAnthropicConfigured ? "Connected" : "Requires Key",
      isConfigured: isAnthropicConfigured,
      isLocal: false,
    },
    {
      provider: "anthropic",
      modelName: "claude-haiku-4-5",
      label: "Anthropic Claude Haiku 4.5",
      type: "cloud",
      badge: isAnthropicConfigured ? "Connected" : "Requires Key",
      isConfigured: isAnthropicConfigured,
      isLocal: false,
    },
  ];

  const currentOption = modelOptions.find(
    (m) => m.provider === selectedModelProvider && m.modelName === selectedModelName
  ) || modelOptions[0];

  const isCurrentSelectionUnconfigured =
    (selectedModelProvider === "openai" && !isOpenAiConfigured) ||
    (selectedModelProvider === "anthropic" && !isAnthropicConfigured) ||
    (selectedModelProvider === "groq" && !isGroqConfigured);

  return (
    <div className="flex-1 h-full flex flex-col bg-[#F4EEE4] text-[#142331] overflow-hidden select-none relative">
      {/* 7A. TOP HEADER: Research Desk */}
      <header className="px-4 sm:px-6 py-2.5 border-b border-[#142331]/10 bg-[#FFF9F0]/90 backdrop-blur-md flex items-center justify-between gap-3 sm:gap-4 shrink-0 z-20 shadow-editorial">
        {/* Left: Research Desk Title & Metadata */}
        <div className="min-w-0 flex-1 pr-2">
          <div className="flex items-center gap-2 min-w-0">
            <h2 className="font-serif text-sm sm:text-base text-[#101B27] truncate font-normal leading-tight">
              {session?.title ? `Research desk • ${session.title}` : "Research desk"}
            </h2>
            <span className="shrink-0 font-mono text-[10px] px-2 py-0.5 rounded-full bg-[#172634] text-[#FFF6E9] hidden sm:inline-flex items-center">
              303 Episodes
            </span>
          </div>
          <p className="text-[11px] text-[#687782] font-sans mt-0.5 truncate hidden sm:block">
            Insights from Lenny's conversations • Turn conversations into clarity.
          </p>
        </div>

        {/* Header Utility Controls */}
        <div className="flex items-center gap-2 sm:gap-2.5 shrink-0">
          {/* Ship 30 Essay Action */}
          <button
            onClick={onOpenShip30}
            className="shrink-0 whitespace-nowrap flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-xl bg-[#FFF9F0] hover:bg-[#101B27] text-[#101B27] hover:text-[#FFF6E9] border border-[#142331]/15 text-xs font-medium shadow-sm transition-all duration-150 group cursor-pointer"
            title="Create an atomic Ship 30 for 30 essay"
            aria-label="Write a Ship 30 essay"
          >
            <PenTool className="w-3.5 h-3.5 text-[#FF7952] shrink-0 group-hover:text-[#FF7952]" />
            <span className="hidden md:inline">Ship 30 essay</span>
            <span className="inline md:hidden">Ship 30</span>
          </button>

          {/* Model Selector Dropdown */}
          <div className="relative shrink-0">
            <button
              onClick={() => setShowModelDropdown(!showModelDropdown)}
              className="shrink-0 whitespace-nowrap flex items-center gap-2 px-2.5 sm:px-3 py-1.5 rounded-xl bg-[#FFF9F0] hover:bg-[#EAE2D5] border border-[#142331]/15 text-xs text-[#142331] font-sans transition shadow-sm cursor-pointer"
              aria-haspopup="true"
              aria-expanded={showModelDropdown}
            >
              {currentOption.isLocal ? (
                <span className="w-2 h-2 rounded-full bg-[#75D2BB] shrink-0" title="Local Model" />
              ) : (
                <Cloud className="w-3.5 h-3.5 text-[#FF7952] shrink-0" />
              )}
              <span className="font-mono text-[11px] font-medium truncate max-w-[110px] sm:max-w-[160px]">
                {currentOption.label}
              </span>
              {isCurrentSelectionUnconfigured && (
                <span className="px-1.5 py-0.2 rounded text-[9px] bg-amber-500/15 text-amber-800 border border-amber-500/30 font-mono shrink-0">
                  Fallback
                </span>
              )}
              <ChevronDown className="w-3 h-3 text-[#687782] shrink-0" />
            </button>

            {showModelDropdown && (
              <div className="absolute right-0 mt-2 w-80 bg-[#172634] text-[#FFF6E9] border border-white/10 rounded-2xl shadow-editorial-lg py-2 z-50 animate-in fade-in zoom-in-95 duration-100">
                {/* Local Models Group */}
                <div className="px-3.5 py-1 text-[10px] font-mono tracking-widest uppercase text-[#75D2BB] flex items-center gap-1.5">
                  <HardDrive className="w-3 h-3" />
                  <span>LOCAL INFERENCE (OLLAMA)</span>
                </div>
                {modelOptions
                  .filter((opt) => opt.type === "local")
                  .map((opt) => {
                    const isSelected =
                      selectedModelProvider === opt.provider && selectedModelName === opt.modelName;
                    return (
                      <button
                        key={`${opt.provider}-${opt.modelName}`}
                        onClick={() => {
                          onSelectModel(opt.provider, opt.modelName);
                          setShowModelDropdown(false);
                        }}
                        className={`w-full text-left px-3.5 py-2 text-xs flex items-center justify-between hover:bg-white/5 transition ${
                          isSelected ? "bg-[#FF7952]/15 text-[#FF7952] font-medium" : "text-[#D7E1D8]"
                        }`}
                      >
                        <div>
                          <div className="font-medium flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#75D2BB]" />
                            {opt.label}
                          </div>
                          <div className="text-[10px] text-[#687782] font-mono pl-3">{opt.badge}</div>
                        </div>
                        {isSelected && <Zap className="w-3.5 h-3.5 text-[#FF7952]" />}
                      </button>
                    );
                  })}

                {/* Cloud Models Group */}
                <div className="px-3.5 pt-2.5 pb-1 text-[10px] font-mono tracking-widest uppercase text-[#FF7952] flex items-center gap-1.5 border-t border-white/5 mt-1">
                  <Cloud className="w-3 h-3" />
                  <span>CLOUD PROVIDERS</span>
                </div>
                {modelOptions
                  .filter((opt) => opt.type === "cloud")
                  .map((opt) => {
                    const isSelected =
                      selectedModelProvider === opt.provider && selectedModelName === opt.modelName;
                    return (
                      <button
                        key={`${opt.provider}-${opt.modelName}`}
                        onClick={() => {
                          onSelectModel(opt.provider, opt.modelName);
                          setShowModelDropdown(false);
                        }}
                        className={`w-full text-left px-3.5 py-2 text-xs flex items-center justify-between hover:bg-white/5 transition ${
                          isSelected ? "bg-[#FF7952]/15 text-[#FF7952] font-medium" : "text-[#D7E1D8]"
                        }`}
                      >
                        <div>
                          <div className="font-medium flex items-center gap-1.5">
                            <Cloud className={`w-3 h-3 ${opt.isConfigured ? "text-[#75D2BB]" : "text-[#687782]"}`} />
                            {opt.label}
                          </div>
                          <div
                            className={`text-[10px] font-mono pl-4.5 ${
                              opt.isConfigured ? "text-[#75D2BB]" : "text-amber-400"
                            }`}
                          >
                            {opt.badge}
                          </div>
                        </div>
                        {isSelected && <Zap className="w-3.5 h-3.5 text-[#FF7952]" />}
                      </button>
                    );
                  })}
              </div>
            )}
          </div>

          {/* Pi SDK Agent Badge / Toggle */}
          <button
            onClick={() => onSelectAgentSdk(agentSdk === "pi" ? "" : "pi")}
            className={`shrink-0 whitespace-nowrap flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-mono transition border cursor-pointer ${
              agentSdk === "pi"
                ? "bg-[#172634] text-[#75D2BB] border-[#75D2BB]/30 shadow-sm"
                : "bg-[#FFF9F0] text-[#687782] border-[#142331]/15 hover:text-[#142331]"
            }`}
            title="Toggle Pi Coding Agent SDK execution"
          >
            <Cpu className="w-3.5 h-3.5 text-[#75D2BB] shrink-0" />
            <span className="text-[11px] font-semibold">Pi SDK</span>
          </button>

          {/* Artifact Studio Toggle Button */}
          <button
            onClick={onToggleArtifact}
            className={`shrink-0 whitespace-nowrap flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 rounded-xl text-xs font-medium transition border shadow-sm cursor-pointer ${
              isArtifactOpen
                ? "bg-[#101B27] text-[#FFF6E9] border-[#101B27]"
                : "bg-[#FFF9F0] text-[#142331] hover:bg-[#EAE2D5] border-[#142331]/15"
            }`}
            title="Toggle Artifact Studio panel"
            aria-label="Toggle Artifact Studio"
          >
            <FileText className="w-3.5 h-3.5 text-[#FF7952] shrink-0" />
            <span className="hidden md:inline">Studio</span>
            {artifactCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-[#FF7952] text-[#101B27] font-bold shrink-0">
                {artifactCount}
              </span>
            )}
          </button>
        </div>
      </header>

      {/* 7B. CONVERSATION STREAM / EMPTY STATE */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-6">
        {messages.length === 0 ? (
          /* Empty State: Editorial Studio Hero */
          <div className="max-w-2xl mx-auto py-10 md:py-16 text-center space-y-8 animate-in fade-in duration-300">
            {/* Custom Abstract Waveform / Growth Vector Graphic */}
            <div className="mx-auto w-24 h-24 rounded-3xl bg-gradient-to-br from-[#FFF9F0] to-[#EAE0D0] border border-[#142331]/10 flex items-center justify-center shadow-editorial p-4 relative group">
              <svg viewBox="0 0 64 64" fill="none" className="w-full h-full">
                <rect x="8" y="32" width="5" height="16" rx="2.5" fill="#687782" opacity="0.4" />
                <rect x="18" y="22" width="5" height="26" rx="2.5" fill="#75D2BB" />
                <rect x="28" y="14" width="5" height="34" rx="2.5" fill="#FF7952" />
                <rect x="38" y="24" width="5" height="24" rx="2.5" fill="#75D2BB" />
                <rect x="48" y="34" width="5" height="14" rx="2.5" fill="#687782" opacity="0.4" />
                {/* Growth curve line */}
                <path
                  d="M10 44C20 40 26 28 40 18L54 10"
                  stroke="#101B27"
                  strokeWidth="3"
                  strokeLinecap="round"
                />
                <circle cx="54" cy="10" r="3.5" fill="#FF7952" />
              </svg>
            </div>

            {/* Editorial Serif Display Heading & Subtitle */}
            <div className="space-y-3">
              <h1 className="font-serif text-3xl md:text-4xl text-[#101B27] font-normal tracking-tight leading-tight">
                Good ideas start with better questions.
              </h1>
              <p className="text-sm md:text-base text-[#4A5B69] max-w-lg mx-auto font-sans leading-relaxed">
                Explore lessons from Lenny's conversations, uncover product insights and turn research into something worth sharing.
              </p>
            </div>

            {/* 4 Clickable Research Starters */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-2 text-left">
              {promptStarters.map((starter) => (
                <button
                  key={starter.title}
                  onClick={() => onSendMessage(starter.query)}
                  className="group p-4 rounded-2xl bg-[#FFF9F0] hover:bg-[#FFFFFF] border border-[#142331]/10 hover:border-[#FF7952]/60 text-left transition-all duration-150 shadow-editorial hover:shadow-editorial-lg flex flex-col justify-between space-y-2 focus-signal"
                  aria-label={`Research prompt: ${starter.title}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-serif text-sm font-medium text-[#101B27] group-hover:text-[#FF7952] transition-colors leading-snug">
                      {starter.title}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#687782] group-hover:text-[#FF7952] group-hover:translate-x-0.5 transition-all shrink-0 mt-0.5" />
                  </div>
                  <p className="text-[11px] text-[#687782] font-mono leading-tight">
                    {starter.tagline}
                  </p>
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Conversation Message Stream */
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg, index) => {
              const isUser = msg.role === "user";
              const citations = msg.citations || [];
              const metadata = msg.metadata || {};
              const toolTrace = metadata.tool_calls_trace || [];
              const isTraceExpanded = expandedTraceIndex === index;

              if (isUser) {
                return (
                  <div key={msg.id || index} className="flex justify-end">
                    <div className="max-w-xl bg-[#172634] text-[#FFF6E9] rounded-2xl rounded-tr-sm px-4.5 py-3 shadow-editorial border border-white/5 space-y-1">
                      <div className="text-[10px] font-mono tracking-wider uppercase text-[#75D2BB]">
                        RESEARCH INQUIRY
                      </div>
                      <p className="text-sm font-sans leading-relaxed whitespace-pre-wrap text-[#FFF6E9]">
                        {msg.content}
                      </p>
                    </div>
                  </div>
                );
              }

              return (
                <div key={msg.id || index} className="flex gap-3.5 items-start">
                  {/* SIGNAL Assistant Monogram Mark */}
                  <div className="w-8 h-8 rounded-xl bg-[#172634] border border-white/10 flex items-center justify-center shrink-0 shadow-sm mt-1">
                    <span className="font-serif text-xs font-bold text-[#FF7952]">S</span>
                  </div>

                  {/* Assistant Reading Card */}
                  <div className="flex-1 min-w-0 bg-[#FFF9F0] border border-[#142331]/10 rounded-2xl p-5 shadow-editorial space-y-4">
                    {/* Header Metadata: Model / Engine / Evidence */}
                    <div className="flex items-center justify-between text-[11px] border-b border-[#142331]/8 pb-2.5">
                      <div className="flex items-center gap-2 font-mono text-[#687782]">
                        <span className="font-semibold text-[#142331]">SIGNAL</span>
                        <span>•</span>
                        <span className="text-[#37947E] font-medium">
                          {metadata.model_provider || selectedModelProvider}: {metadata.model_name || selectedModelName}
                        </span>
                      </div>
                      {metadata.evidence_status && (
                        <span
                          className={`font-mono text-[10px] px-2 py-0.5 rounded-full border ${
                            metadata.evidence_status === "sufficient"
                              ? "bg-[#75D2BB]/15 text-[#37947E] border-[#75D2BB]/30"
                              : "bg-amber-500/15 text-amber-800 border-amber-500/30"
                          }`}
                        >
                          {metadata.evidence_status === "sufficient" ? "Grounded" : "Hypothetical"}
                        </span>
                      )}
                    </div>

                    {/* Multi-turn Tool Trace Inspection */}
                    {toolTrace.length > 0 && (
                      <div className="rounded-xl bg-[#101B27]/5 border border-[#142331]/10 p-2.5 text-xs">
                        <button
                          onClick={() =>
                            setExpandedTraceIndex(isTraceExpanded ? null : index)
                          }
                          className="w-full flex items-center justify-between text-[11px] font-mono text-[#687782] hover:text-[#101B27]"
                        >
                          <span className="flex items-center gap-1.5">
                            <Wrench className="w-3 h-3 text-[#FF7952]" />
                            Transcript Retrieval Trace ({toolTrace.length} tools)
                          </span>
                          {isTraceExpanded ? (
                            <ChevronUp className="w-3 h-3" />
                          ) : (
                            <ChevronDown className="w-3 h-3" />
                          )}
                        </button>
                        {isTraceExpanded && (
                          <div className="mt-2 space-y-1.5 pt-2 border-t border-[#142331]/8 font-mono text-[10px]">
                            {toolTrace.map((call: any, cIdx: number) => (
                              <div key={cIdx} className="bg-[#FFF9F0] p-2 rounded border border-[#142331]/8">
                                <span className="text-[#FF7952] font-semibold">{call.tool}</span>:{" "}
                                <span className="text-[#142331]">{JSON.stringify(call.args)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Markdown Body with Editorial Typography */}
                    <div className="editorial-prose">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>

                    {/* Integrated Signature "Source Tape" Citations */}
                    {citations.length > 0 && (
                      <div className="pt-3 border-t border-[#142331]/8 space-y-2">
                        <div className="flex items-center gap-2 text-[10px] font-mono uppercase tracking-widest text-[#FF7952]">
                          <Radio className="w-3 h-3 text-[#75D2BB]" />
                          <span>SOURCE TAPES ({citations.length} VERIFIED EPISODES)</span>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                          {citations.map((cite, cIdx) => (
                            <CitationCard key={cIdx} citation={cite} index={cIdx} />
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex gap-3.5 items-start animate-in fade-in">
                <div className="w-8 h-8 rounded-xl bg-[#172634] border border-white/10 flex items-center justify-center shrink-0">
                  <span className="font-serif text-xs font-bold text-[#FF7952]">S</span>
                </div>
                <div className="bg-[#FFF9F0] border border-[#142331]/10 rounded-2xl p-4 shadow-editorial flex items-center gap-3 text-xs text-[#142331]">
                  <div className="flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-[#FF7952] animate-bounce" />
                    <span className="w-2 h-2 rounded-full bg-[#75D2BB] animate-bounce [animation-delay:0.2s]" />
                    <span className="w-2 h-2 rounded-full bg-[#172634] animate-bounce [animation-delay:0.4s]" />
                  </div>
                  <span className="font-serif text-xs text-[#4A5B69]">
                    Searching 303 episodes and synthesizing insights...
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* 7D. MESSAGE COMPOSER */}
      <footer className="p-4 md:p-5 bg-gradient-to-t from-[#F4EEE4] via-[#F4EEE4] to-transparent shrink-0">
        <div className="max-w-3xl mx-auto">
          <div className="relative rounded-2xl bg-[#FFF9F0] border border-[#142331]/15 shadow-editorial-lg focus-within:border-[#FF7952] focus-within:ring-2 focus-within:ring-[#FF7952]/20 transition-all p-2">
            <textarea
              ref={textareaRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question. Find the signal."
              rows={2}
              className="w-full bg-transparent resize-none text-sm text-[#142331] placeholder-[#687782]/70 px-3 py-1.5 focus:outline-none font-sans leading-relaxed"
              aria-label="Ask research question"
            />

            <div className="flex items-center justify-between px-2 pt-1 border-t border-[#142331]/8 mt-1 text-[11px] text-[#687782]">
              <div className="flex items-center gap-2 font-mono text-[10px]">
                <span>Grounded on 303 transcripts</span>
                <span>•</span>
                <span>Enter to send, Shift+Enter for newline</span>
              </div>

              <button
                onClick={handleSend}
                disabled={!inputText.trim() || isLoading}
                className="flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#FF7952] hover:bg-[#FF6436] active:scale-95 disabled:opacity-40 disabled:hover:bg-[#FF7952] text-[#101B27] font-semibold text-xs transition-all shadow-sm focus-signal"
                aria-label="Send query"
              >
                <span>Send</span>
                <Send className="w-3.5 h-3.5 stroke-[2.5]" />
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
