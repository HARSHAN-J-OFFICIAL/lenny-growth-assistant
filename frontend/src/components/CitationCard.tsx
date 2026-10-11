import React from "react";
import { ExternalLink, Disc3, Radio } from "lucide-react";
import type { Citation } from "../types";

interface CitationCardProps {
  citation: Citation;
  index?: number;
}

/**
 * Signature Feature: "Source Tape" Citation Card
 * Formats transcript grounding as an archival podcast tape with
 * monospaced source numbering, verified YouTube timestamps, and subtle waveform motif.
 */
export const CitationCard: React.FC<CitationCardProps> = ({ citation, index = 0 }) => {
  const sourceNum = String(index + 1).padStart(2, "0");
  const guest = citation.guest || "Lenny's Podcast";
  const episode = citation.episode_title || "Lenny's Podcast Interview";
  const timestamp = citation.start_timestamp || "00:00:00";
  const hasUrl = Boolean(citation.timestamp_url);

  return (
    <div className="group relative rounded-xl bg-[#FFF9F0] border border-[#142331]/10 hover:border-[#FF7952]/50 p-3 transition-all duration-150 shadow-editorial hover:shadow-editorial-lg text-[#142331] overflow-hidden">
      {/* Decorative subtle tape spool stripe */}
      <div className="absolute top-0 left-0 bottom-0 w-1 bg-gradient-to-b from-[#FF7952] to-[#75D2BB]" />

      <div className="flex items-start justify-between gap-3 pl-1.5">
        <div className="min-w-0 flex-1">
          {/* Tape Header: Monospaced SOURCE Number & Waveform Motif */}
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] tracking-widest font-semibold text-[#FF7952] uppercase">
              SOURCE {sourceNum}
            </span>
            <span className="text-[#687782] text-[10px]">•</span>
            <div className="flex items-center gap-1 text-[11px] font-medium text-[#172634] truncate">
              <Radio className="w-3 h-3 text-[#75D2BB] shrink-0" />
              <span className="truncate">{guest}</span>
            </div>
            {citation.score !== undefined && (
              <span className="ml-auto font-mono text-[9px] px-1.5 py-0.2 rounded bg-[#75D2BB]/15 text-[#37947E] border border-[#75D2BB]/30 shrink-0">
                RRF {citation.score.toFixed(3)}
              </span>
            )}
          </div>

          {/* Episode Title */}
          <p className="text-xs font-serif text-[#142331] leading-snug line-clamp-1 group-hover:text-[#101B27] transition-colors">
            {episode}
          </p>
        </div>

        {/* Timestamp & Direct Link Action */}
        {hasUrl ? (
          <a
            href={citation.timestamp_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#172634] hover:bg-[#FF7952] text-[#FFF6E9] hover:text-[#101B27] text-[11px] font-mono transition-all duration-150 shrink-0 shadow-sm group/link"
            title={`Listen on YouTube at ${timestamp}`}
            aria-label={`Listen to ${guest} on YouTube at timestamp ${timestamp}`}
          >
            <Disc3 className="w-3 h-3 text-[#75D2BB] group-hover/link:text-[#101B27] animate-spin-slow" />
            <span className="font-semibold">{timestamp}</span>
            <ExternalLink className="w-2.5 h-2.5 opacity-80" />
          </a>
        ) : (
          <div className="flex items-center gap-1 px-2 py-1 rounded bg-[#E8E0D2] text-[#687782] text-[10px] font-mono shrink-0">
            <span>{timestamp}</span>
          </div>
        )}
      </div>
    </div>
  );
};
