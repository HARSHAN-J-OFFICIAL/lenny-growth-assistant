/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        signal: {
          shell: "#101B27",          // Midnight Ink (App shell background)
          sidebar: "#172634",        // Secondary dark surface (Sidebar/panels)
          elevated: "#233645",       // Elevated dark surface
          paper: "#F4EEE4",          // Warm Paper (Main content canvas)
          paperLight: "#FFF9F0",     // Light content surface (Editorial reading card)
          coral: "#FF7952",          // Signal Coral (Primary brand accent)
          coralHover: "#FF6436",     // Deeper coral for hover state
          mint: "#75D2BB",           // Mint Signal (Success / Connected systems / Citations)
          mintDark: "#48B49B",       // Mint text on light paper
          sage: "#D7E1D8",           // Neutral sage
          darkText: "#142331",       // Primary dark text (On warm paper)
          mutedDark: "#687782",      // Muted dark text
          lightText: "#FFF6E9",      // Light text (On midnight surfaces)
          borderDark: "rgba(255, 255, 255, 0.08)",
          borderLight: "rgba(20, 35, 49, 0.12)",
        },
      },
      fontFamily: {
        serif: [
          '"DM Serif Display"',
          "Georgia",
          "Cambria",
          "Times New Roman",
          "serif",
        ],
        sans: [
          '"DM Sans"',
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "Roboto",
          "sans-serif",
        ],
        mono: [
          '"IBM Plex Mono"',
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
      boxShadow: {
        "editorial": "0 2px 10px rgba(16, 27, 39, 0.06), 0 1px 3px rgba(16, 27, 39, 0.04)",
        "editorial-lg": "0 10px 30px rgba(16, 27, 39, 0.08), 0 2px 6px rgba(16, 27, 39, 0.04)",
        "coral-glow": "0 4px 18px rgba(255, 121, 82, 0.25)",
        "mint-glow": "0 2px 12px rgba(117, 210, 187, 0.2)",
      },
    },
  },
  plugins: [],
};
