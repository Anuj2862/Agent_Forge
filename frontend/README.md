# Agent Forge — Next.js Frontend Dashboard (Owned by Member 4)

This directory contains the production web dashboard for **Agent Forge**, constructed with Next.js, React, TypeScript, Tailwind CSS, shadcn/ui, and React Flow.

---

## Technical Stack & Libraries
- **Framework**: Next.js (App Router)
- **UI & Components**: React, TypeScript, Tailwind CSS, shadcn/ui
- **Graph Visualization**: React Flow (for dynamic agent network topology rendering)
- **State & Data Fetching**: React Hooks, Axios / Fetch API, WebSockets (planned)

---

## Target Project Structure
```
frontend/
├── app/                  # Next.js App Router (pages & layouts)
│   ├── layout.tsx        # Root layout & theme providers
│   ├── page.tsx          # Main dashboard entrypoint
│   └── history/          # Historical architecture & evolution logs page
├── components/           # UI components
│   ├── architecture/     # React Flow graph visualization components
│   ├── execution/        # Live agent execution status & message stream
│   ├── evaluation/       # Evaluation metrics & quality comparison charts
│   └── ui/               # shadcn/ui base design components
├── lib/                  # API client, WebSocket hooks, and state utilities
├── public/               # Static assets & icons
├── package.json          # Node.js dependencies
└── tsconfig.json         # TypeScript configuration
```

---

## Status
> **Current Phase**: `PLANNED / SCAFFOLDING STAGE` (Initialization assigned to Member 4 on branch `member-4`).
