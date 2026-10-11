import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  FileText,
  Code2,
  Copy,
  Check,
  Download,
  Eye,
  ShieldCheck,
  X,
  PenTool,
} from "lucide-react";
import type { Artifact } from "../types";

interface ArtifactViewerProps {
  artifacts: Artifact[];
  activeArtifactId: string | null;
  onSelectArtifact: (id: string) => void;
  onClose: () => void;
  onGenerateShip30?: () => void;
}

/**
 * Artifact Studio: "From insight to output"
 * A dedicated editorial publishing and artifact rendering studio.
 * Renders structured Markdown essays on Warm Paper surfaces and
 * securely isolates HTML/CSS artifacts in sandboxed iframes.
 */
export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({
  artifacts,
  activeArtifactId,
  onSelectArtifact,
  onClose,
  onGenerateShip30,
}) => {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<"preview" | "source">("preview");

  const currentArtifact = artifacts.find((a) => a.id === activeArtifactId) || artifacts[0];

  const handleCopy = async () => {
    if (!currentArtifact) return;
    try {
      await navigator.clipboard.writeText(currentArtifact.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const handleDownload = () => {
    if (!currentArtifact) return;
    const isHtml = currentArtifact.artifact_type === "html";
    const extension = isHtml ? "html" : "md";
    const mimeType = isHtml ? "text/html" : "text/markdown";
    const filename = `${currentArtifact.title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}.${extension}`;

    const blob = new Blob([currentArtifact.content], { type: `${mimeType};charset=utf-8` });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Securely generate sandboxed HTML iframe document with restrictive CSP
  const generateSandboxedSrcDoc = (content: string) => {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- Restrictive Content Security Policy preventing network calls, scripts, and form actions -->
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'none';">
  <style>
    body {
      font-family: "DM Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #142331;
      background-color: #FFF9F0;
      padding: 32px;
      line-height: 1.7;
      margin: 0;
      word-wrap: break-word;
    }
    h1, h2, h3, h4 { font-family: "DM Serif Display", Georgia, serif; color: #101B27; margin-top: 1.4em; margin-bottom: 0.4em; font-weight: normal; }
    h1 { font-size: 1.8rem; border-bottom: 1px solid rgba(20, 35, 49, 0.12); padding-bottom: 0.3em; }
    h2 { font-size: 1.4rem; }
    h3 { font-size: 1.15rem; }
    p { margin: 0.8em 0; color: #1F3040; }
    ul, ol { padding-left: 1.5em; margin: 0.8em 0; }
    li { margin: 0.3em 0; }
    code { font-family: "IBM Plex Mono", monospace; font-size: 0.88em; background: rgba(20, 35, 49, 0.08); padding: 0.2em 0.4em; border-radius: 4px; }
    pre { background: #172634; color: #FFF6E9; padding: 16px; border-radius: 8px; overflow-x: auto; }
    pre code { background: transparent; color: inherit; padding: 0; }
    blockquote { border-left: 3px solid #FF7952; padding-left: 16px; margin: 1em 0; color: #4A5B69; font-style: italic; background: rgba(255, 121, 82, 0.04); border-radius: 0 6px 6px 0; }
    table { width: 100%; border-collapse: collapse; margin: 1em 0; font-size: 0.9rem; }
    th, td { border: 1px solid rgba(20, 35, 49, 0.15); padding: 8px 12px; text-align: left; }
    th { background: rgba(20, 35, 49, 0.06); font-weight: 600; }
    tr:nth-child(even) { background: rgba(255, 255, 255, 0.5); }
  </style>
</head>
<body>
  ${content}
</body>
</html>`;
  };

  return (
    <aside className="w-full h-full bg-[#172634] text-[#FFF6E9] border-l border-white/5 flex flex-col justify-between overflow-hidden select-none z-10 shadow-editorial-lg">
      {/* Studio Header Bar */}
      <div className="p-4 border-b border-white/5 bg-[#172634]/95 flex items-center justify-between gap-3 shrink-0">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-serif text-base text-[#FFF6E9] truncate font-normal">
              Artifact Studio
            </h3>
            <span className="font-mono text-[9px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-[#FF7952]/15 text-[#FF7952] border border-[#FF7952]/30">
              Publishing
            </span>
          </div>
          <p className="text-[11px] text-[#687782] font-sans truncate">
            From insight to output • Essays & deliverables
          </p>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {onGenerateShip30 && (
            <button
              onClick={onGenerateShip30}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-[#FF7952] hover:bg-[#FF6436] text-[#101B27] font-semibold text-xs shadow-sm transition"
              title="Write a Ship 30 essay"
              aria-label="Write a Ship 30 essay"
            >
              <PenTool className="w-3.5 h-3.5 stroke-[2.5]" />
              <span className="hidden sm:inline">Write Essay</span>
            </button>
          )}

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#687782] hover:text-[#FFF6E9] hover:bg-white/5 transition"
            title="Close Artifact Studio"
            aria-label="Close Artifact Studio"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Artifact Tab Bar (if multiple artifacts exist) */}
      {artifacts.length > 1 && (
        <div className="flex items-center gap-1 overflow-x-auto px-3 py-2 border-b border-white/5 bg-[#101B27]/50 text-xs">
          {artifacts.map((a) => {
            const isSelected = a.id === currentArtifact?.id;
            return (
              <button
                key={a.id}
                onClick={() => onSelectArtifact(a.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-sans text-xs truncate max-w-[180px] transition ${
                  isSelected
                    ? "bg-[#233645] text-[#FFF6E9] font-medium border-b-2 border-[#FF7952]"
                    : "text-[#687782] hover:text-[#D7E1D8] hover:bg-white/5"
                }`}
                title={a.title}
              >
                <FileText className={`w-3 h-3 ${isSelected ? "text-[#FF7952]" : "text-[#687782]"}`} />
                <span className="truncate">{a.title}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Main Studio Canvas */}
      <div className="flex-1 overflow-y-auto bg-[#F4EEE4] text-[#142331] flex flex-col">
        {!currentArtifact ? (
          /* Empty Preview State */
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-5 animate-in fade-in">
            <div className="w-20 h-20 rounded-2xl bg-[#FFF9F0] border border-[#142331]/10 flex items-center justify-center shadow-editorial p-4">
              <svg viewBox="0 0 32 32" fill="none" className="w-full h-full">
                <rect x="6" y="4" width="20" height="24" rx="2" fill="#FFF9F0" stroke="#101B27" strokeWidth="1.5" />
                <line x1="10" y1="10" x2="22" y2="10" stroke="#FF7952" strokeWidth="2" strokeLinecap="round" />
                <line x1="10" y1="15" x2="22" y2="15" stroke="#101B27" strokeWidth="1.5" strokeLinecap="round" opacity="0.6" />
                <line x1="10" y1="20" x2="18" y2="20" stroke="#75D2BB" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </div>
            <div className="space-y-2 max-w-sm">
              <h4 className="font-serif text-xl text-[#101B27] font-normal">
                Your next big idea takes shape here.
              </h4>
              <p className="text-xs text-[#4A5B69] leading-relaxed">
                Generate an essay, explore an insight or create a shareable artifact from podcast transcript research.
              </p>
            </div>
            {onGenerateShip30 && (
              <button
                onClick={onGenerateShip30}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#FF7952] hover:bg-[#FF6436] text-[#101B27] font-semibold text-xs shadow-coral-glow transition"
              >
                <PenTool className="w-3.5 h-3.5 stroke-[2.5]" />
                <span>Write a Ship 30 essay</span>
              </button>
            )}
          </div>
        ) : (
          /* Active Document Preview */
          <div className="flex-1 flex flex-col">
            {/* Document Action Ribbon */}
            <div className="p-3 border-b border-[#142331]/10 bg-[#FFF9F0] flex items-center justify-between text-xs shrink-0">
              <div className="flex items-center gap-2 min-w-0">
                <span className="font-serif font-medium text-sm text-[#101B27] truncate">
                  {currentArtifact.title}
                </span>
                <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 rounded bg-[#101B27]/5 text-[#101B27] border border-[#142331]/10 shrink-0">
                  {currentArtifact.artifact_type}
                </span>
              </div>

              {/* View / Copy / Download actions */}
              <div className="flex items-center gap-1.5 shrink-0">
                {currentArtifact.artifact_type === "html" && (
                  <div className="flex items-center bg-[#EAE2D5] rounded-lg p-0.5 text-xs mr-1">
                    <button
                      onClick={() => setViewMode("preview")}
                      className={`px-2 py-0.5 rounded font-medium text-[11px] transition ${
                        viewMode === "preview" ? "bg-[#101B27] text-[#FFF6E9]" : "text-[#142331]"
                      }`}
                    >
                      <Eye className="w-3 h-3 inline mr-1" />
                      Preview
                    </button>
                    <button
                      onClick={() => setViewMode("source")}
                      className={`px-2 py-0.5 rounded font-medium text-[11px] transition ${
                        viewMode === "source" ? "bg-[#101B27] text-[#FFF6E9]" : "text-[#142331]"
                      }`}
                    >
                      <Code2 className="w-3 h-3 inline mr-1" />
                      Source
                    </button>
                  </div>
                )}

                <button
                  onClick={handleCopy}
                  className="p-1.5 rounded-lg bg-[#EAE2D5] hover:bg-[#DDD5C5] text-[#142331] transition shadow-xs"
                  title="Copy artifact content to clipboard"
                  aria-label="Copy artifact content"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-[#37947E]" /> : <Copy className="w-3.5 h-3.5" />}
                </button>

                <button
                  onClick={handleDownload}
                  className="p-1.5 rounded-lg bg-[#EAE2D5] hover:bg-[#DDD5C5] text-[#142331] transition shadow-xs"
                  title="Download artifact file"
                  aria-label="Download artifact file"
                >
                  <Download className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Document Content */}
            <div className="flex-1 p-6 md:p-8 overflow-y-auto bg-[#FFF9F0]">
              {currentArtifact.artifact_type === "html" && viewMode === "preview" ? (
                /* Secure Sandboxed HTML iFrame */
                <div className="w-full h-full min-h-[500px] border border-[#142331]/10 rounded-xl overflow-hidden shadow-sm bg-white">
                  <iframe
                    title={currentArtifact.title}
                    srcDoc={generateSandboxedSrcDoc(currentArtifact.content)}
                    sandbox=""
                    className="w-full h-full min-h-[500px] border-0"
                  />
                </div>
              ) : currentArtifact.artifact_type === "html" && viewMode === "source" ? (
                /* Raw HTML Code View */
                <pre className="bg-[#172634] text-[#FFF6E9] p-4 rounded-xl text-xs font-mono overflow-x-auto leading-relaxed">
                  <code>{currentArtifact.content}</code>
                </pre>
              ) : (
                /* Typeset Editorial Markdown Preview */
                <div className="editorial-prose max-w-2xl mx-auto">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {currentArtifact.content}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Studio Footer: Security & Word Count */}
      {currentArtifact && (
        <div className="p-3 border-t border-white/5 bg-[#101B27] text-[10px] font-mono text-[#687782] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-1.5 text-[#75D2BB]">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>PostgreSQL Verified Artifact</span>
          </div>
          <div>
            {currentArtifact.content.split(/\s+/).filter(Boolean).length} words
          </div>
        </div>
      )}
    </aside>
  );
};
