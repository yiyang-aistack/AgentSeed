"""AgentSeed — a lightweight, engineering-oriented agent framework on LangGraph.


Package layout (follows 3-layer orthogonal structure):

- ``src.core``      : Framework kernel — domain-independent infrastructure.
- ``src.agents``    : Reusable agent building blocks + framework demo agents(``samples``).
- ``src.capabilities`` : Cross-agent capability assets( tools / MCP / skills).
- ``src.workflows`` : End-user business lines( e.g. testcase / performance), only *compose* agents.
                      ``agents`` + ``capabilities`` + ``core``, no duplication of agent definitions.

Strict conventions
--------
Each concept(agent / tool / skill / workflow) must be defined in exactly one directory.
``agents`` do not overlap with ``workflows``.
"""
