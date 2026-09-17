# AgentSeed UI

[English](README.md) · [简体中文](README.zh-CN.md)

**AgentSeed's bundled chat frontend** — Next.js 16 + React 19 + LangGraph SDK. Your browser connects directly to any LangGraph deployment via HTTP, giving you streaming chat, thread history, multimodal attachments, tool-call visualization, human-in-the-loop (HITL) approvals, and a tasks/files panel.

AgentSeed UI is used to validate AgentSeed's features and performance. In a real delivery the UI is usually **not** shipped as-is: you integrate the backend into your existing business system through the LangGraph Platform REST API (or run it as a microservice), while this UI stays the demo / internal workbench.

> 💡 **For the full AgentSeed project intro, architecture, and backend documentation, see the [root README](../README.md)**.
> This directory is a **standalone application** — it communicates *only* through the LangGraph Platform HTTP API. You can delete this directory and the backend still runs; you can also point this UI at any other LangGraph deployment.
>
> This directory is forked from [langchain-ai/deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui) (MIT), customised for AgentSeed. The package name is now `agentseed-ui`, and licensing follows the repository-wide MIT license. UI copy is primarily in Chinese (see references below), with some buttons staying in English; the root layout at `src/app/layout.tsx` declares `lang="zh-CN"`.

---

![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![LangGraph SDK](https://img.shields.io/badge/LangGraph%20SDK-Client%20%2B%20UI-ff6f61)
![HITL](https://img.shields.io/badge/HITL-Supported-orange)
![Hermes Ready](https://img.shields.io/badge/Hermes%20Agent-Ready-success)
![License](https://img.shields.io/badge/license-MIT-green)

## 🎯 What Can You Build With This UI?

| Scenario | What You Get |
|---|---|
| **Product demo for clients** | Up and running in 10 minutes: streaming chat, tool-call cards, HITL approvals — something polished, functional, and presentable. |
| **Connect your existing Hermes Agent** | Hermes keeps running its own tool loop (no rewrite needed); this UI adds a polished interface + approvals + LangGraph monitoring on top. |
| **Connect other LangGraph deployments** | Not limited to AgentSeed — any LangGraph Platform API-compatible service works with this UI. |
| **Internal agent workbench** | Tasks panel + file viewer + thread history — a visual collaboration surface for your team's agents. |

## 📸 Screenshots

Backend and frontend launching side by side, then the same chat UI talking to two different backends
(a local Ollama agent, and a Hermes Agent — only the AI Worker ID changed):

![AgentSeed backend and frontend starting up](../assets/quickStartup.png)
![Chatting with test_agent in the bundled UI](../assets/agentUI_llm.png)
![The same UI bridged to a Hermes Agent, only the AI Worker ID changed](../assets/agentUI_integration.png)

> The UI copy in these screenshots is Chinese (`lang="zh-CN"` in `src/app/layout.tsx`); the images
> themselves live in the repository root's `assets/` directory.

---

## ✨ Features

### Chat & Conversations

- Streaming conversation with a configured **AI Worker** (LangGraph deployment + assistant); messages auto-stick-to-bottom (`use-stick-to-bottom`).
- **Conversation persistence**: the current thread ID lives in the URL query parameter `threadId` — refresh or switch conversation and it restores (`reconnectOnMount`, `fetchStateHistory`).
- Top-bar **Chat History** button opens the thread history sidebar (URL param `sidebar=1`). The button shows a badge counting how many currently loaded items have `status=interrupted`.
- History sidebar (`ThreadList`): title `History`, status filter `All / Idle / Busy / Interrupted / Error`, time-grouped `Needs Attention / Today / Yesterday / This Week / Earlier`, scroll-paginated (20 per page), single-thread delete with a confirmation prompt.
- Top-bar **Setting** opens the configuration dialog; top-bar ✏️ (SquarePen) starts a new conversation (clears `threadId`, disabled when no thread exists).

### Attachments & Multimodal

- Three ways to add files: click **Upload PDF or image files**, drag & drop into the input area, or paste directly into the input box.
- Supported MIME types: `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `application/pdf` (see `SUPPORTED_FILE_TYPES`). Invalid types and duplicate files trigger a `sonner` toast.
- Preview and remove attachments before sending (`ContentBlocksPreview` / `MultimodalPreview`).
- Transport: images travel as `image_url` (data URL, OpenAI-compatible) inside `message.content`; PDFs go into `message.additional_kwargs.attachments` for the backend to parse.

### Message Rendering

- Markdown + GFM (`react-markdown` + `remark-gfm`), code-block syntax highlighting (Prism / oneDark theme).
- User-side images preview inline via data URL; PDFs render as cards.
- **Tool calls** (`ToolCallBox`): status icons (`pending` / `completed` / `error` / `interrupted`), each call expandable to show *Arguments* and *Result*.
- Custom backend-supplied UI components are rendered as GenUI through `LoadExternalComponent` (`@langchain/langgraph-sdk/react-ui`).
- **Sub-agents**: `task` tool calls with a `subagent_type` render as `SubAgentIndicator` cards, expandable to show *Input* / *Output*.

### Human-in-the-loop (HITL) Interrupts

- Parses the Deep Agents interrupt protocol `{ action_requests, review_configs }`, and shows approve / edit / reject buttons according to `review_configs[].allowed_decisions` (all three shown when unconfigured).
- Tool-call cards embed `ToolApprovalInterrupt`: **Approve**, **Edit** (edit args → *Save and Approve*), **Reject** (fill in reason + confirmation dialog).
- Decisions are sent back as `command: { resume: { decisions: [...] } }`, with `type` being `approve` / `edit` (with `edited_action`) / `reject` (with `message`).
- Note: the repo also contains `InterruptActions` (multi-decision "submit all at once" component), which is not yet wired into the UI.

### Tasks & Files Panel

- Collapsible panel above the input box: **Tasks** (`todos`, grouped into *Pending / In Progress / Completed*) and **Files (Status)** (`files`, with count badge).
- File viewer (`FileViewDialog`): view / edit / copy / download. `.md` / `.markdown` files render as Markdown; everything else is syntax-highlighted by extension. Editing is blocked while streaming or when an interrupt is pending.

### Miscellaneous

- **Send** → **Stop** while running — interrupt the stream mid-response.
- Friendly backend-connectivity errors (e.g. `ConnectError` → a Chinese-language hint that the LangGraph server cannot reach the LLM service; see the FAQ).
- Resizable left/right panels with auto-save (`react-resizable-panels`, `autoSaveId="standalone-chat"`).
- Theme colours live in CSS variables inside `src/app/globals.css` (dark variants included). `tailwind.config.mjs` `darkMode` supports both `class` and `[data-joy-color-scheme="dark"]`, but there is no UI toggle yet.

---

## 🧱 Tech Stack

| Area | Choices |
|---|---|
| Framework | Next.js 16 (App Router / Turbopack) + React 19 + TypeScript |
| Styling | Tailwind CSS 3 + shadcn/ui (Radix UI), `sonner` toasts |
| LangGraph | `@langchain/langgraph-sdk` (`useStream`, `Client`, `LoadExternalComponent`), `@langchain/core` |
| Others | `nuqs` (URL query state), `swr` (thread list / file save), `react-markdown` + `remark-gfm`, `react-syntax-highlighter`, `react-resizable-panels`, `use-stick-to-bottom`, `date-fns`, `lucide-react` |

## 🚀 Quick Start

### Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Node.js | ≥ 20 | See `.nvmrc` in this directory |
| yarn | 1.22.22 | Specified in `package.json` `packageManager`. Repo ships both `yarn.lock` and `package-lock.json`. |
| AgentSeed backend | — | Recommended to start it first from the repo root with `uv run backend/main.py`. You can also point this UI at any other LangGraph Platform deployment. |

### Step 1 — Install dependencies

```bash
cd frontend
yarn install
```

### Step 2 — Start the dev server

```bash
yarn dev          # default: http://localhost:3000
```

✅ **Verify** — open `http://localhost:3000`. The **Configuration** dialog appears on first load.

### Step 3 — Configure and connect to the backend

Two required fields in the Configuration dialog:

| Field | UI Label | Value when connecting to AgentSeed backend |
|---|---|---|
| `deploymentUrl` | **AI Worker URL** | `http://localhost:2026` |
| `assistantId` | **AI Worker ID** | Any graph name registered in the root `agentConfig.yaml`, e.g. `test_agent` / `hermes_agent` |

> 💡 **Connecting Hermes Agent?** Fill in `hermes_agent` as the AI Worker ID and this UI will talk directly to the bridged Hermes Agent. Hermes keeps its own tools / skills / memory running — you do **not** change anything on the Hermes side. Full bridge configuration is documented in the root README.

✅ **Try it** — type *"What's the weather in Shanghai today?"* → you'll see a tool-call card transition from *pending* to *completed* and then the final reply.

Config is stored in browser `localStorage` under `agentseed-config`; click **Setting** in the top bar to change it anytime.

### Production build

```bash
yarn build
yarn start
```

Other scripts: `yarn lint`, `yarn lint:fix`, `yarn format`, `yarn format:check`.

### Integration scenarios

| Scenario | AI Worker URL | AI Worker ID | Notes |
|---|---|---|---|
| AgentSeed local default | `http://localhost:2026` | `test_agent` | Local Ollama model, zero config |
| Hermes Agent (via bridge) | `http://localhost:2026` | `hermes_agent` | Hermes keeps its own runtime; this UI is just the interface |
| Other LangGraph deployments | Your LangGraph API URL | Your graph name or assistant UUID | Any LangGraph Platform-compatible service |

### Configuration fields (`StandaloneConfig`)

| Field | UI Label | Required | Notes |
|---|---|---|---|
| `deploymentUrl` | **AI Worker URL** | ✅ | LangGraph deployment URL. The SDK connects directly from the browser — CORS must be enabled. |
| `assistantId` | **AI Worker ID** | ✅ | Graph name (e.g. `test_agent`) or assistant UUID. When it's a UUID, the SDK calls `assistants.get` directly; otherwise it calls `assistants.search` and picks the default. |
| `langsmithApiKey` | — (no input box in UI) | ❌ | Sent as `x-api-key` header when present; recommend supplying it via the environment variable below. |

Request headers always include `Content-Type: application/json` and `x-auth-scheme: langsmith` (see `src/providers/ClientProvider.tsx`).

### Environment variables

```env
# Optional: LangSmith API Key (the UI input for this field is currently commented out)
NEXT_PUBLIC_LANGSMITH_API_KEY="lsv2_..."
```

> Priority: `localStorage` config > environment variables. `deploymentUrl` and `assistantId` can *only* be set through the Configuration dialog — `src/lib/config.ts` does not read environment variables for them.

### URL query parameters (shareable / bookmarkable)

| Param | Notes |
|---|---|
| `threadId` | Current thread ID (managed by `nuqs`) |
| `assistantId` | Current AI Worker ID |
| `sidebar` | Open thread history sidebar when `1` |

---

## 🔌 Backend Contract (LangGraph Deployment)

### State fields (`StateType`, see `src/app/hooks/useChat.ts`)

| Field | Type | Purpose |
|---|---|---|
| `messages` | `Message[]` | Conversation messages (required) |
| `todos` | `TodoItem[]` | Tasks panel. `status` is one of `pending` / `in_progress` / `completed`. |
| `files` | `Record<string, string>` | Files panel + file viewer |
| `ui` | `any[]` | GenUI components, linked to a message or tool call via `metadata.message_id` / `metadata.tool_call_id` |
| `email` | `{ id?, subject?, page_content? }` | Read by the hook but not rendered in the current UI |

- Every send / resume call submits with `recursion_limit: 100`.
- Thread listing is ordered by `updated_at desc`, 20 per page. When `assistantId` is a UUID it filters by `metadata.assistant_id` (locally-developed graphs don't write that metadata).

### HITL interrupt protocol

```jsonc
{
  "action_requests": [
    { "name": "some_tool", "args": {}, "description": "Explain what the tool does" }
  ],
  "review_configs": [
    {
      "action_name": "some_tool",
      "allowed_decisions": ["approve", "edit", "reject"]
    }
  ]
}
```

User decisions are sent back via `command.resume` (see `src/app/components/ToolApprovalInterrupt.tsx`):

```jsonc
{ "decisions": [{ "type": "approve" }] }
{ "decisions": [{ "type": "edit", "edited_action": { "name": "some_tool", "args": {} } }] }
{ "decisions": [{ "type": "reject", "message": "Reason (can be empty)" }] }
```

Type definitions live in `src/app/types/inbox.ts`: `HumanInterrupt` / `HumanInterruptConfig` / `HumanResponse`.

### Attachment transport

| Type | Location | Format |
|---|---|---|
| Image | `message.content[]` | `{ type: "image_url", image_url: { url: "data:<mime>;base64,..." } }` (OpenAI-compatible) |
| PDF | `message.additional_kwargs.attachments` | `{ type: "file", mimeType: "application/pdf", data: "<base64>", metadata: { filename } }` — parsed by the backend |

## 📁 Directory Structure

Config files: `next.config.ts` (empty), `tailwind.config.mjs`, `postcss.config.cjs`, `eslint.config.js`, `prettier.config.cjs`, `components.json` (shadcn/ui config), `tsconfig.json` (path alias `@/*` → `./src/*`).

---

## 🖥️ UI Copy Quick Reference

| Location | Copy | Behaviour |
|---|---|---|
| Top bar | `AgentSeed UI` | App title |
| Top bar | `Chat History` | Toggle thread history sidebar, with interrupted-thread-count badge |
| Top bar | `AI Worker: <assistantId>` | Shows current AI Worker |
| Top bar | `Setting` | Open configuration dialog |
| Top bar | ✏️ icon | New conversation (clears `threadId`) |
| History sidebar | `History` + status dropdown | `All / Idle / Busy / Interrupted / Error` |
| Input box | `Please input your message...` / `Running...` | Enter to send, `Shift + Enter` for newline |
| Input box | `Upload PDF or image files` | Pick attachments (multi-select) |
| Input box | `Send` / `Stop` | Send / interrupt streaming output |
| Collapsible panel | `Tasks` / `Files (Status)` | View `todos` and `files` |
| File viewer | `Enter filename...` / `Enter file content...` | Edit and save file |
| Tool approval | `Approval Required` / `Approve` / `Edit` / `Reject` | Approve execution, edit args (save and approve), reject with reason |

---

## ❓ FAQ

- **"Backend LangGraph server cannot connect to the LLM service"** — the backend deployment's model API key or network is the issue (the frontend translates `ConnectError` into this hint in Chinese). If you are using the `hermes_agent` bridge, also verify that Hermes Agent's API server is up (`API_SERVER_ENABLED=true`) and its token matches `API_SERVER_KEY` in the root `.env`.
- **No response / empty thread list** — confirm the AI Worker URL is reachable *from the browser* with CORS enabled, and that the AI Worker ID matches a registered graph name or assistant UUID.
- **Attachments rejected** — only JPEG / PNG / GIF / WEBP / PDF are accepted. Duplicate filenames within one message are flagged.
- **File cannot be edited** — the file viewer is read-only while streaming or when an interrupt is pending.
- **Port already in use** — default is 3000; pick another with `npx next dev -p 3001`.
- **Hermes Agent won't connect** — the `hermes_agent` bridge requires all of `HERMES_BASE_URL`, `API_SERVER_KEY`, `HERMES_MODEL`, and `HERMES_TIMEOUT` in the root `.env`. Missing any one triggers an explicit error at backend startup (see the Configuration section in the root README).

---

## 💬 Want to Customize This UI?

AgentSeed's frontend is a standalone app and can be adapted to your needs:

- Connect your existing Hermes Agent or other LangGraph deployments
- Change UI copy, brand colours, and layout
- Add custom tool-call cards and GenUI components
- Production deployment (Docker + Nginx + TLS)

For the full AgentSeed collaboration and reach-out, see the root README's [Want a Custom Build?](../README.md) section.

---

## 📄 License & Copyright

- This directory uses the **MIT** license, consistent with the rest of the repository (see [`LICENSE`](../LICENSE) at the repo root).
- Source-file headers are owned by **JunSu - AI** and declared with `SPDX-License-Identifier: MIT`. They also retain the upstream [deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui) MIT attribution (Copyright (c) 2025 LangChain).
- For commercial partnerships or sub-licensing, contact **JunSu - AI**.

