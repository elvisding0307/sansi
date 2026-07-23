"""Backward-compatible Agent wrapper replacing ``openai-agents`` ``Agent`` class.

Used by legacy text-based agent files (tagline_agent, company_overview_agent, etc.)
to store instructions and output types without depending on the ``openai-agents`` package.
"""

from typing import Optional, Type


class LangChainAgent:
    """Minimal drop-in replacement for openai-agents ``Agent``.

    Stores name, instructions, and optional output_type so the legacy module-level
    agent objects keep working.  Actual execution is handled by
    ``EquityResearchAgentManager.generate_text_section()``, which does not use these
    objects at all — they exist only for backward-compatible imports.
    """

    def __init__(
        self,
        name: str,
        instructions: str,
        output_type: Optional[Type] = None,
    ):
        self.name = name
        self.instructions = instructions
        self.output_type = output_type
