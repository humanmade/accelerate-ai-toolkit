"""Accelerate AI Toolkit — Hermes plugin.

Auto-registers every skill under ../skills/ as a Hermes skill. Skills live
alongside this manifest at the repo root (`skills/`), shared with the Claude,
Cursor, Codex, Gemini, and GitHub Copilot client manifests. Hermes loads them
on demand via:

    skill_view("accelerate-ai-toolkit:<skill-name>")

The WordPress connection (the `wordpress` MCP server every skill depends on)
is configured separately in Hermes — see .hermes-plugin/README.md.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# The plugin folder is `.hermes-plugin/`, which sits next to `skills/` in the
# accelerate-ai-toolkit repo. install.sh symlinks .hermes-plugin/ into
# ~/.hermes/plugins/, so resolve() before walking up — otherwise the parent is
# the symlink directory (~/.hermes/plugins) and skills/ is missing.
_PLUGIN_DIR = Path(__file__).resolve().parent
_SKILLS_DIR = _PLUGIN_DIR.parent / "skills"


def _discover_skills() -> list[tuple[str, Path]]:
    """Return (skill_name, SKILL.md path) for every shared skill."""
    if not _SKILLS_DIR.is_dir():
        logger.warning("skills/ directory missing at %s", _SKILLS_DIR)
        return []

    found: list[tuple[str, Path]] = []
    for child in sorted(_SKILLS_DIR.iterdir()):
        if not child.is_dir():
            continue
        skill_md = child / "SKILL.md"
        if skill_md.is_file():
            found.append((child.name, skill_md))
        else:
            logger.debug("Skipping %s — no SKILL.md", child.name)
    return found


def register(ctx) -> None:
    """Hermes entry point. Called once at startup."""
    skills = _discover_skills()
    for skill_name, skill_md in skills:
        ctx.register_skill(skill_name, skill_md)
    logger.info("accelerate-ai-toolkit: registered %d skills", len(skills))
