# Design Specification & UI/UX Principles
## SIGNAL — The Lenny Growth Studio (The Lenny Growth Assistant)
**Identity & Tagline:** SIGNAL — The Lenny Growth Studio (*"Turn conversations into clarity."*)  
**Author / Role:** Principal Product Designer & Forward Deployed Engineer (FDE)  
**Aesthetic Direction:** Editorial Modernist / High-Precision Audio Research Studio  

---

## 1. Design Philosophy & Creative Vision

SIGNAL transforms The Lenny Growth Assistant from a generic conversational chatbot into a distinctive, publication-grade research workspace and editorial studio. Inspired by the visual discipline of premium editorial publications (*The Atlantic*, *The New Yorker*, *Stripe Press*), modern audio production studios, and high-end productivity workstations (*Linear*, *Raycast*, *iA Writer*):

1. **Warm Paper Reading Surface (`#F4EEE4` / `#FFF9F0`)**:
   - Long-form transcript synthesis, product frameworks, and 1,250-word essays belong on a calm, high-contrast editorial paper surface.
   - Eliminates eye strain and the sterile, terminal-like feel of generic dark AI dashboards.

2. **Midnight Ink Structural Shell (`#101B27` / `#172634` / `#233645`)**:
   - Structural framing, navigation, and persistent research notebooks reside on deep Midnight Ink surfaces.
   - Creates an intentional contrast boundary that directs focus inward toward the central research desk and publication artifacts.

3. **Intentional Accent Calibration**:
   - **Signal Coral (`#FF7952`)**: Exclusively reserved for primary user intent—initiating a new session, dispatching a research query, and generating a Ship 30 essay. Never applied as ambient decoration.
   - **Mint Signal (`#75D2BB`)**: Denotes system liveliness, validated transcript citations, connected local/cloud inference models, and successful background persistence.

4. **Deliberate Three-Tier Typography System**:
   - **Display Typography (`DM Serif Display`)**: Editorial serif applied selectively to the empty-state hero (*"Good ideas start with better questions."*), major article headers, and modal brief titles.
   - **UI Typography (`DM Sans`)**: Contemporary, high-legibility geometric sans-serif applied to navigation, buttons, chat dialogues, form controls, and status labels.
   - **Technical Typography (`IBM Plex Mono`)**: Precise monospace applied to podcast timestamps (`00:04:15`), Source Tape index numbers (`SOURCE 01`), model identifiers, and citation RRF confidence scores.

---

## 2. Design System & Token Architecture

```css
:root {
  /* Midnight Ink Shell & Framing */
  --signal-shell: #101B27;
  --signal-sidebar: #172634;
  --signal-elevated: #233645;

  /* Warm Paper Reading Surfaces */
  --signal-paper: #F4EEE4;
  --signal-paper-light: #FFF9F0;

  /* Accents */
  --signal-coral: #FF7952;
  --signal-coral-hover: #FF6436;
  --signal-mint: #75D2BB;
  --signal-sage: #D7E1D8;

  /* Typography Colors */
  --signal-dark-text: #142331;
  --signal-muted-dark: #687782;
  --signal-light-text: #FFF6E9;
}
```

| Token | Value | Semantic Role |
| :--- | :--- | :--- |
| `signal.shell` | `#101B27` | Deepest canvas background, shell divider frames |
| `signal.sidebar` | `#172634` | Research Library panel, modal headers, dark elevated cards |
| `signal.elevated` | `#233645` | Dropdown surfaces, hover rows, card containers |
| `signal.paper` | `#F4EEE4` | Central AI research workspace canvas |
| `signal.paperLight`| `#FFF9F0` | Assistant response reading cards, form inputs |
| `signal.coral` | `#FF7952` | Primary action buttons, active tab indicators, CTAs |
| `signal.mint` | `#75D2BB` | Local Ollama active status, validated citations |
| `signal.sage` | `#D7E1D8` | Low-contrast borders on warm paper |
| `signal.darkText` | `#142331` | High-contrast editorial body copy on paper |
| `signal.mutedDark`| `#687782` | Secondary metadata, timestamps, author attribution |
| `signal.lightText`| `#FFF6E9` | Primary typography on Midnight Ink surfaces |

---

## 3. Information Architecture (Three-Panel Resizable Workspace)

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Top Research Bar: Signal Brand Mark | "Research desk" Subtitle | Model Selector | Panel Toggle Controls │
├───────────────────────┬───────────────────────────────────────────┬────────────────────────────────────┤
│ Panel 1: Research     │ Panel 2: AI Research Workspace            │ Panel 3: Artifact Studio           │
│ Library (Sidebar)     │ (Center Canvas - Warm Paper)              │ (Right Panel - Editorial Output)   │
│                       │                                           │                                    │
│ - Brand Header:       │ - Header: "Research desk" / Subtitle      │ - Header: Title | Type Badge       │
│   Signal Logo +       │ - Empty State Hero:                       │ - Actions: [Preview] | [Source]    │
│   "LENNY GROWTH       │   • Inline SVG geometric growth waveform  │            [Copy]    | [Download]  │
│    STUDIO"            │   • "Good ideas start with better         │ - Content Canvas:                  │
│ - Primary Action:     │      questions."                          │   • Typeset Markdown Essay         │
│   "+ New conversation"│   • 4 Editorial Prompt Starter Cards      │     (.editorial-prose)             │
│   (Signal Coral)      │ - Chat Feed:                              │   • OR Sandboxed HTML/CSS Iframe   │
│ - Session History:    │   • User Query Pill (Midnight Ink)        │     (sandbox="" + strict CSP)      │
│   • Compact rows      │   • Assistant Reading Card (Paper Light)  │ - Footer: Word Count Badge &       │
│   • Thin Coral active │   • Source Tapes (Podcast Citations with  │   Security Sandbox Indicator       │
│     indicator marker  │     timestamps & YouTube deep-links)      │                                    │
│   • Hover rename /    │ - Message Composer:                       │                                    │
│     delete controls   │   • Elevated warm input with focus ring   │                                    │
│ - Footer:             │   • "Ask a question. Find the signal."    │                                    │
│   Provider & model    │   • Compact Coral send button             │                                    │
│   operational status  │   • "Write a Ship 30 essay" trigger       │                                    │
└───────────────────────┴───────────────────────────────────────────┴────────────────────────────────────┘
```

---

## 4. Signature Components

### 4.1 Custom Signal Brand Mark (`SignalLogo.tsx`)
- An original inline SVG composition blending an audio waveform, an ascending growth signal, and a clean editorial monogram.
- Renders consistently in header navigation, compact mobile drawers, and full desktop headers without relying on external image CDNs.

### 4.2 Podcast Source Citations — "Source Tapes" (`CitationCard.tsx`)
- Structured as compact, cassette-inspired audio reference tapes.
- Features:
  - Monospaced badge index (`SOURCE 01`, `SOURCE 02`).
  - Episode title and guest attribution in crisp editorial typography.
  - Monospaced timestamp pill (e.g., `00:04:15`).
  - Clickable external link arrow (`↗ Listen on YouTube`) navigating to the exact playback second (`&t={s}s`).
  - Calibrated Reciprocal Rank Fusion ($RRF$) relevance score badge.

### 4.3 Centered Floating Ship 30 Modal (`Ship30Modal.tsx`)
- Opens centered in the viewport with a soft backdrop blur (`bg-[#101B27]/70 backdrop-blur-sm`).
- Styled as an author's writing brief: *"Make something worth reading."* (*"Turn the best ideas from Lenny's conversations into a compelling Ship 30 essay."*).
- Inputs styled on warm light surfaces (`#FFF9F0`) with dark readable text, avoiding jarring white form boxes.
- Full keyboard support: native `Escape` to close, outside-click detection, and `Enter` dispatch.
- Dispatches to the 120-second timeout-budgeted `/api/v1/skills/ship30` endpoint and automatically opens the finished essay in the Artifact Studio.

### 4.4 Artifact Studio (`ArtifactViewer.tsx`)
- Subtitled *"From insight to output"*.
- Renders 1,250+ word essays and research briefs on warm paper with drop caps, structured subheaders, and verified guest citations using `.editorial-prose`.
- Sandboxed HTML/CSS preview isolated in an `<iframe>` with `sandbox=""` and a Content Security Policy of `default-src 'none'; style-src 'unsafe-inline'; img-src data:; form-action 'none';`.
- Interactive toolbar offering word count calculations, one-click clipboard copy with visual feedback, and `.md` file download.

---

## 5. Viewport Adaptation & Responsive Breakpoints

1. **Desktop Ultra / Wide (1440px+)**:
   - Complete three-panel resizable workstation: Sidebar (260px–440px), Center Research Desk (flex), Artifact Studio (360px–850px).
   - Horizontal drag handle with mouse-move tracking and boundary clamping.

2. **Laptop Standard (1024px–1366px)**:
   - Three-panel layout with dynamic center canvas contraction.
   - Quick header toggle buttons to collapse either panel for focused reading.

3. **Tablet (768px–1024px)**:
   - Center conversation prioritized; sidebar collapses to an accessible sliding drawer.
   - Artifact Studio toggles smoothly via workspace header controls.

4. **Mobile (390px–767px)**:
   - Single-column zero-horizontal-overflow layout.
   - Header drawer toggles for conversation history.
   - Artifact Studio renders as an animated full-screen modal with sticky action controls.

---

## 6. Accessibility & Usability (WCAG 2.1 AA Compliance)

- **Contrast Ratios**: All body text on Warm Paper exceeds 7:1 (WCAG AAA); interactive controls exceed 4.5:1 (WCAG AA).
- **Focus Rings**: High-visibility focus indicators (`focus-visible:ring-2 focus-visible:ring-[#FF7952]`) on textareas, buttons, dropdowns, and links.
- **Keyboard Navigation**: Full keyboard tab sequence through prompt starters, model dropdowns, citation links, and modal dialogues.
- **Reduced Motion**: All CSS transitions respect `prefers-reduced-motion: reduce`.
- **Informative Status States**: No state conveyed by color alone; text labels and badges accompany all icons.
