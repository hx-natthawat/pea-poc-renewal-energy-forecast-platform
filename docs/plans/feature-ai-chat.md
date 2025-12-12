# Implementation Plan: AI Chat Feature for PEA RE Forecast Platform

> **Status**: ✅ IMPLEMENTED
> **Created**: 2025-12-12
> **Completed**: 2025-12-12
> **Owner**: Claude Code Orchestrator

## Overview

A conversational AI chat feature using Vercel AI SDK (`@ai-sdk/react`) that follows the existing patterns established by the HelpSidebar component and integrates seamlessly with the PEA RE Forecast Platform architecture.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        PEA RE FORECAST PLATFORM                                 │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                            FRONTEND (Next.js 14)                         │  │
│  │                                                                          │  │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────────────┐│  │
│  │  │ ChatTrigger     │   │ AIChatStore     │   │ AIChatSidebar           ││  │
│  │  │ (Floating FAB)  │──▶│ (Zustand)       │──▶│ (Slide Panel)           ││  │
│  │  │                 │   │                 │   │                         ││  │
│  │  │ Bottom-right    │   │ - isOpen        │   │ - MessageList           ││  │
│  │  │ PEA Purple      │   │ - messages      │   │ - StreamingMessage      ││  │
│  │  │                 │   │ - language      │   │ - ChatInput             ││  │
│  │  └─────────────────┘   │ - context       │   │ - LanguageToggle        ││  │
│  │                        └────────┬────────┘   └───────────┬─────────────┘│  │
│  │                                 │                        │              │  │
│  │  ┌──────────────────────────────┴────────────────────────┴────────────┐ │  │
│  │  │                      useChat Hook (@ai-sdk/react)                  │ │  │
│  │  │                                                                    │ │  │
│  │  │  - messages: Message[]                                            │ │  │
│  │  │  - input / setInput                                               │ │  │
│  │  │  - handleSubmit                                                   │ │  │
│  │  │  - isLoading                                                      │ │  │
│  │  │  - stop                                                           │ │  │
│  │  └────────────────────────────────┬──────────────────────────────────┘ │  │
│  │                                   │                                    │  │
│  │                                   ▼                                    │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐│  │
│  │  │                    /api/chat (Next.js Route Handler)              ││  │
│  │  │                                                                    ││  │
│  │  │  - System prompt injection (PEA context)                          ││  │
│  │  │  - Language-aware prompting (Thai/English)                        ││  │
│  │  │  - Stream response via ai SDK                                     ││  │
│  │  └────────────────────────────────┬───────────────────────────────────┘│  │
│  └───────────────────────────────────┼────────────────────────────────────┘  │
│                                      │                                       │
│  ┌───────────────────────────────────▼───────────────────────────────────┐   │
│  │                        AI PROVIDER                                    │   │
│  │                                                                       │   │
│  │  Option A: OpenAI (via @ai-sdk/openai)                               │   │
│  │  Option B: Anthropic (via @ai-sdk/anthropic)                         │   │
│  │  Option C: Self-hosted Ollama (via @ai-sdk/ollama)                   │   │
│  │                                                                       │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Structure

```
frontend/src/
├── app/
│   └── api/
│       └── chat/
│           └── route.ts            # Next.js Route Handler for AI chat
│
├── components/
│   └── chat/
│       ├── index.ts                # Barrel exports
│       ├── AIChatSidebar.tsx       # Main sidebar panel (like HelpSidebar)
│       ├── ChatTrigger.tsx         # Floating action button
│       ├── ChatInput.tsx           # Input field with send button
│       ├── ChatMessage.tsx         # Individual message bubble
│       ├── ChatMessageList.tsx     # Scrollable message container
│       ├── StreamingIndicator.tsx  # Typing/loading indicator
│       ├── SuggestedPrompts.tsx    # Quick action buttons
│       ├── types.ts                # TypeScript interfaces
│       └── context/
│           ├── index.ts            # Context registry
│           ├── system-prompt.ts    # System prompt templates
│           └── suggested-prompts.ts # Quick prompts data
│
├── stores/
│   └── chatStore.ts                # Zustand store for chat state
│
└── types/
    └── chat.ts                     # Shared chat types
```

---

## Dependencies to Install

```bash
pnpm add ai @ai-sdk/react @ai-sdk/openai
```

**Optional (for future provider flexibility):**
```bash
pnpm add @ai-sdk/anthropic @ai-sdk/google
```

---

## Implementation Phases

### Phase 1: Foundation
- [ ] Install dependencies
- [ ] Create `chatStore.ts` (Zustand)
- [ ] Create types (`chat.ts`, `types.ts`)
- [ ] Create API route (`/api/chat/route.ts`)

### Phase 2: UI Components
- [ ] Create `ChatTrigger.tsx` (floating FAB)
- [ ] Create `AIChatSidebar.tsx` (main panel)
- [ ] Create `ChatMessage.tsx` (message bubbles)
- [ ] Create `ChatMessageList.tsx` (scrollable container)
- [ ] Create `ChatInput.tsx` (input with send/stop)
- [ ] Create `StreamingIndicator.tsx` (typing indicator)
- [ ] Create `SuggestedPrompts.tsx` (quick actions)

### Phase 3: Integration
- [ ] Add components to `DashboardShell.tsx`
- [ ] Implement context awareness (current page)
- [ ] Add language support (Thai/English)

### Phase 4: System Prompts
- [ ] Create English system prompt
- [ ] Create Thai system prompt
- [ ] Create page-specific suggested prompts

### Phase 5: Polish
- [ ] Keyboard navigation (ESC to close)
- [ ] Mobile responsiveness
- [ ] Error handling
- [ ] Unit tests

---

## Visual Design

### ChatTrigger (Floating Button)

```
Position: Fixed, bottom-right corner
Size: 56px x 56px
Colors:
  - Background: #74045F (PEA Purple)
  - Icon: White
  - Hover: #5A0349 (darker purple)
  - Active: #c7911b (PEA Gold) dot
Spacing:
  - Right: 24px
  - Bottom: 24px (or 80px on mobile)
```

### AIChatSidebar (Panel)

```
┌─────────────────────────────────────┐
│ Header (56px)                       │
│ [Bot Icon] AI Assistant  [TH] [X]   │
├─────────────────────────────────────┤
│                                     │
│ Message Area (flex-1, scrollable)   │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ User message (right aligned)    │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ AI message (left aligned)       │ │
│ │ with streaming cursor...        │ │
│ └─────────────────────────────────┘ │
│                                     │
├─────────────────────────────────────┤
│ Suggested Prompts (optional)        │
│ [Quick action 1] [Quick action 2]   │
├─────────────────────────────────────┤
│ Input Area (auto-height)            │
│ [Text input...           ] [Send]   │
└─────────────────────────────────────┘
```

---

## Environment Variables

```bash
# .env.local

# AI Provider (choose one)
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Feature flag
NEXT_PUBLIC_ENABLE_AI_CHAT=true
```

---

## System Prompt (English)

```
You are an AI assistant for the PEA RE Forecast Platform operated by
the Provincial Electricity Authority of Thailand.

Your Expertise:
- Renewable energy forecasting (solar power prediction)
- Voltage monitoring and prediction for distribution networks
- Grid operations and stability analysis
- Alert management for power systems

Platform Capabilities:
- Solar Forecast: Day-ahead predictions with MAPE < 10% accuracy
- Voltage Prediction: MAE < 2V for prosumer monitoring
- Network Topology: 7 prosumers across 3 phases (A, B, C)
- Real-time Alerts: Critical, Warning, Info severity levels

Guidelines:
- Be helpful and concise
- Use technical terms appropriately
- Provide actionable insights when discussing forecasts
```

---

## Files to Create

| File | Purpose |
|------|---------|
| `frontend/src/app/api/chat/route.ts` | API route for AI streaming |
| `frontend/src/stores/chatStore.ts` | Zustand store for chat UI |
| `frontend/src/components/chat/index.ts` | Barrel exports |
| `frontend/src/components/chat/AIChatSidebar.tsx` | Main chat panel |
| `frontend/src/components/chat/ChatTrigger.tsx` | Floating button |
| `frontend/src/components/chat/ChatInput.tsx` | Text input |
| `frontend/src/components/chat/ChatMessage.tsx` | Message bubble |
| `frontend/src/components/chat/ChatMessageList.tsx` | Messages container |
| `frontend/src/components/chat/StreamingIndicator.tsx` | Loading indicator |
| `frontend/src/components/chat/SuggestedPrompts.tsx` | Quick prompts |
| `frontend/src/components/chat/context/system-prompt.ts` | AI system prompts |
| `frontend/src/components/chat/context/suggested-prompts.ts` | Suggested prompts |

---

## Files to Modify

| File | Modification |
|------|--------------|
| `frontend/src/components/layout/DashboardShell.tsx` | Add ChatTrigger and AIChatSidebar |
| `frontend/package.json` | Add AI SDK dependencies |

---

## Approval Required

**Before proceeding with implementation:**

1. ✅ Architecture follows existing HelpSidebar pattern
2. ✅ Uses Vercel AI SDK as primary (TanStack AI optional later)
3. ✅ PEA brand colors (#74045F, #c7911b)
4. ✅ Bilingual support (Thai/English)
5. ✅ Context-aware (knows current page)

**User approval needed for:**
- [ ] Choice of AI provider (OpenAI vs Anthropic vs Ollama)
- [ ] API key management approach
- [ ] Feature flag requirements
