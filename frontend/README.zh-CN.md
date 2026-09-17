# AgentSeed UI

[English](README.md) · [简体中文](README.zh-CN.md)

**AgentSeed 自带的聊天前端** — Next.js 16 + React 19 + LangGraph SDK，浏览器直连任意 LangGraph
部署，提供流式对话、会话历史、多模态附件、工具调用可视化、人机协同（HITL）审批、任务/文件面板。

> 💡 **完整的 AgentSeed 项目介绍、架构与后端文档见 [仓库根 README](../README.md)**。
> 本目录是 **独立应用**：只通过 LangGraph Platform HTTP API 通信，删除本目录后端仍可运行，
> 本 UI 也可以对接任意其他 LangGraph 部署。
>
> 本目录由 [langchain-ai/deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui)（MIT）
> 定制而来，包名改为 `agentseed-ui`，授权遵循仓库根目录的 MIT 许可。界面文案以中文为主，
> 根布局 `src/app/layout.tsx` 中为 `lang="zh-CN"`。

---

![Next.js](https://img.shields.io/badge/Next.js-16-000000?logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)
![LangGraph SDK](https://img.shields.io/badge/LangGraph%20SDK-Client%20%2B%20UI-ff6f61)
![HITL](https://img.shields.io/badge/HITL-Supported-orange)
![Hermes Ready](https://img.shields.io/badge/Hermes%20Agent-Ready-success)
![License](https://img.shields.io/badge/license-MIT-green)

## 🎯 这个 UI 能用来做什么？

| 场景 | 你得到什么 |
|---|---|
| **产品 Demo 给客户看** | 10 分钟内跑起来：流式聊天、工具调用卡片、HITL 审批 — 现成的、好看的、能跑的 |
| **对接你的 Hermes Agent** | Hermes 继续跑自己的 tool loop（不用重写），本 UI 给它加上漂亮界面 + 审批 + LangGraph 监控 |
| **对接其他 LangGraph 部署** | 不只 AgentSeed — 任何 LangGraph Platform API 兼容服务都能接上本 UI |
| **团队内部 agent 工作台** | 任务面板 + 文件查看器 + 会话历史 — 可视化协作界面 |

## 📸 界面截图

后端与前端并排启动，以及同一个聊天界面分别对接两种后端（本地 Ollama agent，以及 Hermes Agent
—— 唯一的变化是 AI Worker ID）：

![AgentSeed 后端与前端启动](../assets/quickStartup.png)
![在自带界面里和 test_agent 对话](../assets/agentUI_llm.png)
![同一个界面桥接到 Hermes Agent，只改了 AI Worker ID](../assets/agentUI_integration.png)

> 截图中的界面文案为中文（根布局 `src/app/layout.tsx` 中 `lang="zh-CN"`），
> 图片文件位于仓库根目录的 `assets/` 下。

---

## ✨ 功能一览

### 对话与会话

- 与指定的 **AI Worker**（LangGraph 部署 + assistant）流式对话，消息自动吸底（`use-stick-to-bottom`）。
- 会话持久化：当前会话 ID 存在 URL 查询参数 `threadId` 中，刷新或切换会话可恢复（`reconnectOnMount`、`fetchStateHistory`）。
- 顶栏 **Chat History** 展开会话历史侧栏（URL 参数 `sidebar=1`），按钮右侧带"当前已加载列表中 `status=interrupted` 会话数"的徽标。
- 历史侧栏（`ThreadList`）：标题 `History`，状态筛选 `All / Idle / Busy / Interrupted / Error`，按时间分组 `需要关注 / 今天 / 昨天 / 本周 / 更早`，滚动分页（每页 20 条），单条删除（二次确认 `Are you sure you want to permanently delete this history?`）。
- 顶栏 **Setting** 打开配置对话框；顶栏 ✏️（SquarePen）按钮新建对话（清空 `threadId`，无会话时禁用）。

### 附件与多模态

- 三种添加方式：点击 **Upload PDF or image files**、拖拽到输入框区域、在输入框中直接粘贴。
- 支持类型：`image/jpeg`、`image/png`、`image/gif`、`image/webp`、`application/pdf`（见 `SUPPORTED_FILE_TYPES`）；非法类型与重复文件会通过 `sonner` toast 提示。
- 发送前可预览并逐项移除（`ContentBlocksPreview` / `MultimodalPreview`）。
- 传输方式：图片以 `image_url`（data URL，OpenAI 兼容）进入 `message.content`；PDF 放入 `message.additional_kwargs.attachments` 交由后端解析。

### 消息渲染

- Markdown + GFM（`react-markdown` + `remark-gfm`），代码块语法高亮（Prism / oneDark 主题）。
- 用户消息中的图片以 data URL 直接预览，PDF 以卡片形式展示。
- **工具调用**（`ToolCallBox`）：显示状态图标（pending / completed / error / interrupted），可逐项展开查看"参数"与"结果"。
- 若后端返回自定义 UI 组件，则通过 `LoadExternalComponent`（`@langchain/langgraph-sdk/react-ui`）渲染 GenUI。
- **子智能体**：`task` 工具且带 `subagent_type` 的调用会以 `SubAgentIndicator` 展示，可展开查看"输入 / 输出"。

### 人机协同（HITL）中断

- 解析 Deep Agents 中断协议 `{ action_requests, review_configs }`，按 `review_configs[].allowed_decisions`（`approve` / `edit` / `reject`）决定显示哪些按钮（未配置时三个都显示）。
- 工具调用卡片内嵌 `ToolApprovalInterrupt`：**批准**、**编辑**（改完参数点"保存并批准"）、**拒绝**（可填写拒绝原因，二次确认）。
- 决策以 `command: { resume: { decisions: [...] } }` 回传，`type` 分别为 `approve` / `edit`（附 `edited_action`）/ `reject`（附 `message`）。
- 说明：仓库中另有 `InterruptActions`（支持一次提交多个中断的"提交全部决策"），当前未被界面引用。

### 任务与文件面板

- 输入框上方的折叠面板：**任务**（`todos`，按 待处理 / 进行中 / 已完成 分组）与 **文件 (状态)**（`files`，带数量徽标）。
- 文件查看器（`FileViewDialog`）：查看 / 编辑 / 复制 / 下载；`.md` / `.markdown` 走 Markdown 渲染，其他按扩展名语法高亮；流式运行中或存在中断时禁止编辑。

### 其它

- 运行中 **Send** 变为 **Stop**，可中断流式输出。
- 后端连接异常有友好提示（如 `ConnectError` → "后端 LangGraph 服务器无法连接到 LLM 服务。请检查后端配置的 API Key 和网络连接。"）。
- 左右面板可拖拽调整宽度并自动记忆（`react-resizable-panels`，`autoSaveId="standalone-chat"`）。
- 主题色集中在 `src/app/globals.css` 的 CSS 变量中（含 dark 变量）；`tailwind.config.mjs` 的 `darkMode` 支持 `class` 与 `[data-joy-color-scheme="dark"]`，当前界面未提供切换开关。

---

## 🧱 技术栈

| 领域      | 选型                                                                                                                                                                                           |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 框架      | Next.js 16（App Router / Turbopack）+ React 19 + TypeScript                                                                                                                                    |
| 样式      | Tailwind CSS 3 + shadcn/ui（Radix UI）、`sonner` 提示                                                                                                                                          |
| LangGraph | `@langchain/langgraph-sdk`（`useStream`、`Client`、`LoadExternalComponent`）、`@langchain/core`                                                                                                |
| 其它      | `nuqs`（URL 查询状态）、`swr`（会话列表 / 文件保存）、`react-markdown` + `remark-gfm`、`react-syntax-highlighter`、`react-resizable-panels`、`use-stick-to-bottom`、`date-fns`、`lucide-react` |

## 🚀 快速开始

### Prerequisites

| 工具 | 版本 | 说明 |
|---|---|---|
| Node.js | ≥ 20 | 见本目录 `.nvmrc` |
| yarn | 1.22.22 | `package.json` 的 `packageManager` 指定；仓库同时保留 `yarn.lock` 与 `package-lock.json` |
| AgentSeed 后端 | — | 推荐先在仓库根目录 `uv run backend/main.py` 启动；也可以对接任意 LangGraph Platform 部署 |

### Step 1 — 安装依赖

```bash
cd frontend
yarn install
```

### Step 2 — 启动开发服务器

```bash
yarn dev          # 默认 http://localhost:3000
```

✅ **验证** — 打开 `http://localhost:3000`，首次加载会弹出 **Configuration** 对话框

### Step 3 — 配置并连接后端

Configuration 对话框的两项必填字段：

| 字段 | 界面名称 | 对接 AgentSeed 后端时填 |
|---|---|---|
| `deploymentUrl` | **AI Worker URL** | `http://localhost:2026` |
| `assistantId` | **AI Worker ID** | 根目录 `agentConfig.yaml` 中注册的图名，如 `test_agent` / `hermes_agent` |

> 💡 **对接 Hermes Agent**：把 AI Worker ID 填 `hermes_agent`，本 UI 就会直连到桥接后的 Hermes Agent。
> Hermes 自己的工具/skills/memory 照常运行，审批流和界面体验由本 UI 提供 — 你**不用改 Hermes**，
> 根 README 有完整的桥接配置说明。

✅ **Try it** — 输入 *"今天上海天气怎么样？"* → 你会看到工具调用卡片（pending → completed）和最终回复。

配置保存在浏览器 `localStorage` 的 `agentseed-config` 键下，之后可随时点击顶栏 **Setting** 修改。

### 生产构建

```bash
yarn build
yarn start
```

其它脚本：`yarn lint`、`yarn lint:fix`、`yarn format`、`yarn format:check`。

### 对接方式对照

| 场景 | AI Worker URL | AI Worker ID | 备注 |
|---|---|---|---|
| AgentSeed 本地默认 | `http://localhost:2026` | `test_agent` | Ollama 本地模型，零配置 |
| 对接 Hermes Agent（桥接） | `http://localhost:2026` | `hermes_agent` | Hermes 自己的运行时继续，本 UI 只做界面 |
| 其他 LangGraph 部署 | 你的 LangGraph API 地址 | 你的图名或 assistant UUID | 任意 LangGraph Platform 兼容服务 |

### 配置项（`StandaloneConfig`）

| 字段              | 界面名称              | 必填 | 说明                                                                                                               |
| ----------------- | --------------------- | ---- | ------------------------------------------------------------------------------------------------------------------ |
| `deploymentUrl`   | **AI Worker URL**     | ✅   | LangGraph 部署地址。浏览器通过 SDK 直连该地址，需允许跨域（CORS）                                                  |
| `assistantId`     | **AI Worker ID**      | ✅   | 图名（如 `research`）或 assistant UUID；为 UUID 时直接 `assistants.get`，否则 `assistants.search` 取默认 assistant |
| `langsmithApiKey` | —（界面未提供输入框） | ❌   | 存在时作为 `x-api-key` 请求头发送；建议通过下方环境变量提供                                                        |

请求头统一包含 `Content-Type: application/json` 与 `x-auth-scheme: langsmith`（`src/providers/ClientProvider.tsx`）。

### 环境变量

```env
# 可选：LangSmith API Key（界面上的该输入项当前被注释掉）
NEXT_PUBLIC_LANGSMITH_API_KEY="lsv2_..."
```

> 优先级：`localStorage` 中的配置 > 环境变量。`deploymentUrl` 与 `assistantId` 只能通过配置对话框设置（`src/lib/config.ts` 不读取环境变量）。

### URL 查询参数（可分享 / 收藏）

| 参数          | 说明                               |
| ------------- | ---------------------------------- |
| `threadId`    | 当前会话 ID（由 `nuqs` 管理）      |
| `assistantId` | 当前 AI Worker ID                  |
| `sidebar`     | 是否展开会话历史侧栏（`1` 为展开） |

---

## 🔌 后端（LangGraph 部署）契约

### 状态字段（`StateType`，见 `src/app/hooks/useChat.ts`）

| 字段       | 类型                               | 用途                                                                                  |
| ---------- | ---------------------------------- | ------------------------------------------------------------------------------------- |
| `messages` | `Message[]`                        | 对话消息（必需）                                                                      |
| `todos`    | `TodoItem[]`                       | 任务面板，`status` 为 `pending` / `in_progress` / `completed`                         |
| `files`    | `Record<string, string>`           | 文件面板与文件查看器                                                                  |
| `ui`       | `any[]`                            | GenUI 组件，通过 `metadata.message_id` / `metadata.tool_call_id` 关联到消息或工具调用 |
| `email`    | `{ id?, subject?, page_content? }` | Hook 中已读取，当前界面未渲染                                                         |

- 每次发送 / 继续时提交参数带 `recursion_limit: 100`。
- 列举历史会话按 `updated_at desc` 排序、每页 20 条；当 `assistantId` 为 UUID 时按 `metadata.assistant_id` 过滤（本地开发的图不写该 metadata）。

### 中断（HITL）协议

```jsonc
{
  "action_requests": [
    { "name": "some_tool", "args": {}, "description": "说明" }
  ],
  "review_configs": [
    {
      "action_name": "some_tool",
      "allowed_decisions": ["approve", "edit", "reject"]
    }
  ]
}
```

用户决策以如下形式随 `command.resume` 回传（见 `src/app/components/ToolApprovalInterrupt.tsx`）：

```jsonc
{ "decisions": [{ "type": "approve" }] }
{ "decisions": [{ "type": "edit", "edited_action": { "name": "some_tool", "args": {} } }] }
{ "decisions": [{ "type": "reject", "message": "拒绝原因（可为空）" }] }
```

类型定义见 `src/app/types/inbox.ts`：`HumanInterrupt` / `HumanInterruptConfig` / `HumanResponse`。

### 附件传输

| 类型 | 位置                                    | 格式                                                                                                                     |
| ---- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 图片 | `message.content[]`                     | `{ type: "image_url", image_url: { url: "data:<mime>;base64,..." } }`（OpenAI 兼容，代码注释面向豆包 / OpenAI 兼容接口） |
| PDF  | `message.additional_kwargs.attachments` | `{ type: "file", mimeType: "application/pdf", data: "<base64>", metadata: { filename } }`，由后端解析                    |

## 📁 目录结构

```
src/
├─ app/
│  ├─ page.tsx                     # 首页：顶栏、配置对话框、会话历史 + 聊天（可拖拽分栏）
│  ├─ layout.tsx                   # 根布局：Inter 字体、nuqs 适配器、sonner Toaster，lang="zh-CN"
│  ├─ globals.css                  # 主题 CSS 变量与全局样式
│  ├─ components/
│  │  ├─ ChatInterface.tsx         # 聊天主体：消息列表、输入框、附件上传、任务/文件折叠面板、Send/Stop
│  │  ├─ ChatMessage.tsx           # 单条消息：用户/AI、图片/PDF、工具调用、子智能体
│  │  ├─ ToolCallBox.tsx           # 工具调用卡片（参数/结果、GenUI、审批入口）
│  │  ├─ ToolApprovalInterrupt.tsx # 工具审批 UI（批准/编辑/拒绝）
│  │  ├─ InterruptActions.tsx      # Deep Agents 中断操作组件（当前未被界面引用）
│  │  ├─ SubAgentIndicator.tsx     # 子智能体指示器
│  │  ├─ MarkdownContent.tsx       # Markdown + 代码高亮
│  │  ├─ MultimodalPreview.tsx     # 图片/PDF 预览与移除
│  │  ├─ ContentBlocksPreview.tsx  # 发送前的附件预览列表
│  │  ├─ TasksFilesSidebar.tsx     # FilesPopover（文件面板，已接入）+ TasksFilesSidebar（备用，当前未被引用）
│  │  ├─ FileViewDialog.tsx        # 文件查看/编辑/复制/下载
│  │  ├─ ThreadList.tsx            # 会话历史侧栏（筛选/分组/分页/删除）
│  │  └─ ConfigDialog.tsx          # 配置对话框（AI Worker URL / AI Worker ID）
│  ├─ hooks/
│  │  ├─ useChat.ts                # useStream 封装：发送/停止/中断恢复，读取 todos、files、ui
│  │  ├─ useThreads.ts             # 会话列表（SWR 无限分页）
│  │  └─ useFileUpload.ts          # 附件选择/拖拽/粘贴与去重
│  ├─ types/
│  │  ├─ types.ts                  # ToolCall、SubAgent、TodoItem、FileItem、ActionRequest、ReviewConfig 等
│  │  └─ inbox.ts                  # 中断协议类型（HumanInterrupt / HumanResponse 等）
│  └─ utils/
│     ├─ utils.ts                  # 消息内容提取、格式化等工具
│     └─ multimodal.ts             # File → ContentBlock、类型判断
├─ components/ui/                  # shadcn/ui 基础组件（button、dialog、input、label、resizable、
│                                  #   scroll-area、select、skeleton、switch、tabs、textarea、tooltip 等）
├─ providers/
│  ├─ ClientProvider.tsx           # 单例 LangGraph SDK Client（apiUrl + 请求头）
│  └─ ChatProvider.tsx             # useChat 上下文（ChatProvider / useChatContext）
└─ lib/
   ├─ config.ts                    # localStorage 配置读写（键：agentseed-config）
   └─ utils.ts                     # cn(...) 类名合并
```

配置文件：`next.config.ts`（空配置）、`tailwind.config.mjs`、`postcss.config.cjs`、`eslint.config.js`、`prettier.config.cjs`、`components.json`（shadcn/ui 配置）、`tsconfig.json`（路径别名 `@/*` → `./src/*`）。

---

## 🖥️ 界面文案速查

| 位置       | 文案                                          | 行为                                             |
| ---------- | --------------------------------------------- | ------------------------------------------------ |
| 顶栏       | `AgentSeed UI`                    | 应用标题                                         |
| 顶栏       | `Chat History`                                | 展开/收起会话历史侧栏，带中断会话数徽标          |
| 顶栏       | `AI Worker: <assistantId>`                    | 显示当前 AI Worker                               |
| 顶栏       | `Setting`                                     | 打开配置对话框                                   |
| 顶栏       | ✏️ 图标                                       | 新建对话（清空 `threadId`）                      |
| 历史侧栏   | `History` + 状态下拉                          | `All / Idle / Busy / Interrupted / Error`        |
| 输入框     | `Please input your message...` / `Running...` | 回车发送，`Shift + 回车`换行                     |
| 输入框     | `Upload PDF or image files`                   | 选择附件（可多选）                               |
| 输入框     | `Send` / `Stop`                               | 发送 / 中断流式输出                              |
| 折叠面板   | `任务` / `文件 (状态)`                        | 查看 `todos` 与 `files`                          |
| 文件查看器 | `输入文件名...` / `输入文件内容...`           | 编辑并保存文件                                   |
| 工具审批   | `需要批准` / `批准` / `编辑` / `拒绝`         | 批准执行、编辑参数（保存并批准）、拒绝并说明原因 |

---

## ❓ 常见问题

- **提示"后端 LangGraph 服务器无法连接到 LLM 服务"**：后端部署侧的模型 API Key 或网络异常（前端把 `ConnectError` 转成了中文提示）。若对接的是 `hermes_agent` 桥接，还需确认 Hermes Agent 的 API server 是否已启动（`API_SERVER_ENABLED=true`）且 token 与根仓库 `.env` 中 `API_SERVER_KEY` 一致。
- **对话无响应 / 会话列表为空**：确认 AI Worker URL 可从浏览器直接访问且已开启 CORS，且 `AI Worker ID` 与部署中的图名或 assistant UUID 一致。
- **附件被拒绝**：仅支持 JPEG / PNG / GIF / WEBP / PDF；同一条消息内同名文件会提示重复。
- **文件无法编辑**：流式运行中或存在中断时，文件编辑器为只读。
- **端口被占用**：默认 3000，可指定端口：`npx next dev -p 3001`。
- **Hermes Agent 连不上**：`hermes_agent` 桥接需要 `.env` 中 `HERMES_BASE_URL`、`API_SERVER_KEY`、`HERMES_MODEL`、`HERMES_TIMEOUT` 全部配置。缺任何一个后端启动时会明确报错（见根 README 的 Configuration section）。

---

## 💬 想定制这个 UI？

AgentSeed 的前端是独立应用，可以按你的业务场景定制：

- 对接你已有的 Hermes Agent 或其他 LangGraph 部署
- 修改界面文案、品牌色、布局
- 增加专属的工具调用卡片、GenUI 组件
- 生产部署（Docker + Nginx + TLS）

完整的 AgentSeed 定制协作见 [根 README 的 "Want a Custom Build?"](../README.md)。

---

## 📄 许可证与版权

- 本目录与仓库其余部分统一采用 **MIT** 许可（见仓库根目录 [`LICENSE`](../LICENSE)）。
- 各源码文件头部版权归 **JunSu - AI**，并以
  `SPDX-License-Identifier: MIT` 声明；头部同时保留上游
  [deep-agents-ui](https://github.com/langchain-ai/deep-agents-ui) 的 MIT 署名
  （Copyright (c) 2025 LangChain）。
- 商业合作 / 二次授权请联系 **JunSu - AI**。