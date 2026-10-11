import React from "react";

interface SignalLogoProps {
  size?: "sm" | "md" | "lg";
  showWordmark?: boolean;
  showSubtitle?: boolean;
  className?: string;
}

/**
 * SIGNAL Brand Mark:
 * A distinctive editorial monogram harmonizing an audio waveform
 * and an ascending exponential growth vector in Signal Coral (#FF7952)
 * and Mint Signal (#75D2BB).
 */
export const SignalLogo: React.FC<SignalLogoProps> = ({
  size = "md",
  showWordmark = true,
  showSubtitle = true,
  className = "",
}) => {
  const iconSizes = {
    sm: "w-7 h-7",
    md: "w-9 h-9",
    lg: "w-11 h-11",
  };

  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Custom Audio Waveform + Growth Vector Mark */}
      <div
        className={`${iconSizes[size]} rounded-xl bg-gradient-to-br from-[#172634] to-[#233645] border border-white/10 p-1.5 flex items-center justify-center shrink-0 shadow-editorial relative overflow-hidden group`}
      >
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full"
        >
          {/* Subtle audio waveform bars */}
          <rect x="4" y="16" width="2.5" height="7" rx="1.25" fill="#687782" opacity="0.6" />
          <rect x="9" y="11" width="2.5" height="12" rx="1.25" fill="#75D2BB" />
          <rect x="14" y="7" width="2.5" height="16" rx="1.25" fill="#FF7952" />
          <rect x="19" y="12" width="2.5" height="11" rx="1.25" fill="#75D2BB" />
          <rect x="24" y="17" width="2.5" height="6" rx="1.25" fill="#687782" opacity="0.6" />

          {/* Ascending Growth Signal Vector Line */}
          <path
            d="M4 22L10 16L15 19L26 8"
            stroke="#FFF6E9"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Beacon dot at peak of growth signal */}
          <circle cx="26" cy="8" r="2" fill="#FF7952" />
        </svg>
      </div>

      {showWordmark && (
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-serif text-base tracking-wider text-[#FFF6E9] font-normal leading-none">
              SIGNAL
            </span>
            <span className="text-[9px] font-mono tracking-widest uppercase px-1.5 py-0.5 rounded bg-[#FF7952]/15 text-[#FF7952] border border-[#FF7952]/30 leading-none">
              STUDIO
            </span>
          </div>
          {showSubtitle && (
            <div className="text-[10px] font-sans tracking-wide text-[#687782] uppercase mt-1 leading-tight truncate">
              The Lenny Growth Studio
            </div>
          )}
        </div>
      )}
    </div>
  );
};
