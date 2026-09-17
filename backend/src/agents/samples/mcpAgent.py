"""
Copyright (c) 2023-2026 钧朔 - JunSu - AI
Released under the MIT License.
See LICENSE file for full license text.

MCP-backed agent — its tools live on an external MCP server, not in this process.

``localAgent`` binds tools from the in-process registry
(``src.capabilities.tools``). This sample shows the other half of the capability
layer: the tools come from an **MCP server** declared in
``src/capabilities/mcp/servers.yaml`` — here Tavily's hosted remote MCP, which
serves ``tavily-search`` / ``tavily-extract`` / ``tavily-map`` /
``tavily-crawl`` over streamable HTTP.

Note what this file does *not* contain: no HTTP client, no endpoint, no API key,
no tool schema. It asks the capability layer for tools by server name — exactly
the way ``localAgent`` asks the registry for ``"weather"`` — and binds them to a
``create_agent`` loop. Swapping Tavily for another MCP server, or for a local
stdio one, is a ``servers.yaml`` edit; the agent code does not change.

Why this graph degrades instead of failing loudly
-------------------------------------------------
``hermesAgent`` refuses to start when its ``.env`` settings are missing, because
those settings are static configuration that only the user can supply. Tavily is
different in one decisive way: it is a *remote third-party endpoint* reached over
the network. Aborting the import here would take down the four unrelated graphs
sharing this server whenever the network hiccups or no key is configured yet.
So the failure is separated by cause:

- **Not configured / unreachable** → the agent is still built, without MCP tools,
  and the reason is logged at ERROR with the exact fix. The server and every
  other graph keep working.
- **Misconfigured** (bad transport, missing ``url``, unknown server name) → still
  logged loudly, same path, because that is a ``servers.yaml`` bug to fix.

Either way the log line, not a silent fallback, is what tells you the tools are
gone — and the system prompt states it too, so the model says "I cannot search"
instead of inventing an answer.

The compiled agent is exported as a **real module-level attribute** ``mcp_agent``:
``langgraph_api`` resolves a registered graph with
``module.__dict__[spec.variable]`` and never triggers a PEP 562 ``__getattr__``,
so a lazy-only export would make the server fail with "Could not find graph".
"""

from __future__ import annotations

import logging

logger = logging.getLogger("agentseed.agents.mcpAgent")

# Name of the server in src/capabilities/mcp/servers.yaml. Changing MCP providers
# is a change to that file, not to this one.
MCP_SERVER = "tavily"

# Base persona. The MCP-specific clause is appended only when the tools actually
# loaded, so the model never promises a capability that is not bound.
_SYSTEM_PROMPT = (
    "You are a research assistant with web-search tools from the Tavily MCP "
    "server. Use them whenever the answer depends on current or external "
    "information, and cite the source URLs you retrieved. Use current_date when "
    "the question depends on today's date."
)
# Appended when the MCP tools are unavailable: saying so beats guessing.
_NO_MCP_NOTE = (
    " Web search is unavailable in this run, so answer from your own knowledge "
    "and state clearly that you could not verify anything online."
)


def _load_mcp_tools() -> list:
    """Fetch the MCP server's tools, or ``[]`` with a loud log when unavailable.

    Kept as its own function so the three failure modes (not enabled, not
    configured, unreachable) all funnel through one place that cannot raise.
    """
    from src.capabilities.mcp import tools as mcp_tools
    from src.capabilities.mcp.manager import MCPConfigError

    try:
        return mcp_tools(MCP_SERVER)
    except KeyError:
        # The server is commented out or disabled in servers.yaml.
        logger.error(
            "MCP server %r is not enabled in servers.yaml — building the graph "
            "without its tools. Set `enabled: true` for it to restore them.",
            MCP_SERVER,
        )
    except MCPConfigError as exc:
        # Enabled but under-configured (usually an unset .env placeholder).
        logger.error("MCP server %r is misconfigured: %s", MCP_SERVER, exc)
    except Exception:
        # Reached the network and did not get a usable answer (DNS, TLS, 401,
        # timeout, …). Unexpected, so keep the traceback.
        logger.exception(
            "Could not load tools from MCP server %r — building the graph without "
            "them. Check the network and the credentials in .env.",
            MCP_SERVER,
        )
    return []


def _build_agent():
    """Import heavy providers and compile the agent (called once, at import)."""
    from langchain.agents import create_agent

    from src.capabilities.tools import builtin
    from src.core.llm import build_chat_model

    mcp_tool_list = _load_mcp_tools()
    if mcp_tool_list:
        logger.info(
            "MCP server %r contributed %d tool(s): %s",
            MCP_SERVER,
            len(mcp_tool_list),
            ", ".join(tool.name for tool in mcp_tool_list),
        )

    # Registry tools and MCP tools are interchangeable here — both are plain
    # BaseTool objects, which is the point of keeping MCP behind the capability
    # layer. current_date stays bound either way: it is process-local, so it
    # works even when the MCP server does not.
    tools = [*builtin(["current_date"]), *mcp_tool_list]

    return create_agent(
        model=build_chat_model(),  # shared, memoized — see src.core.llm
        tools=tools,
        system_prompt=_SYSTEM_PROMPT + ("" if mcp_tool_list else _NO_MCP_NOTE),
    )


# Must be a REAL module-level attribute: langgraph_api resolves a registered
# graph via `module.__dict__[spec.variable]`, which never triggers PEP 562
# `__getattr__`. See the module docstring.
mcp_agent = _build_agent()


__all__ = ["mcp_agent"]
