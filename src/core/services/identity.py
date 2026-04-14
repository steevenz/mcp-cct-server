import os
import logging
from pathlib import Path
from typing import Dict

from src.core.models.identity_defaults import SOVEREIGN_MINDSET, SOVEREIGN_SOUL

logger = logging.getLogger(__name__)

class IdentityService:
    """
    Manages the Identity Layer (Digital Symbiosis).
    Responsible for provisioning default assets and loading the identity context for sessions.
    """

    def __init__(self, identity_dir: str = "configs/identity"):
        self.identity_dir = Path(identity_dir)
        self.mindset_path = self.identity_dir / "mindset.md"
        self.soul_path = self.identity_dir / "soul.md"

    def provision_assets(self) -> None:
        """
        Auto-seeds the identity directory with sovereign defaults if missing.
        Ensures a 'Zero-Config' experience for the user.
        """
        try:
            if not self.identity_dir.exists():
                logger.info(f"[IDENTITY] Creating directory: {self.identity_dir}")
                self.identity_dir.mkdir(parents=True, exist_ok=True)

            if not self.mindset_path.exists():
                logger.info(f"[IDENTITY] Seeding sovereign mindset: {self.mindset_path}")
                self.mindset_path.write_text(SOVEREIGN_MINDSET, encoding="utf-8")

            if not self.soul_path.exists():
                logger.info(f"[IDENTITY] Seeding CCT soul: {self.soul_path}")
                self.soul_path.write_text(SOVEREIGN_SOUL, encoding="utf-8")

        except Exception as e:
            logger.error(f"[IDENTITY] Failed to provision assets: {e}")
            # Non-fatal: we will fall back to constants during load_identity if files are missing

    def load_identity(self) -> Dict[str, str]:
        """
        Loads the mindset and soul context.
        Prioritizes files, falls back to hardcoded DNA if files are unreadable.
        """
        identity = {
            "user_mindset": SOVEREIGN_MINDSET,
            "cct_soul": SOVEREIGN_SOUL
        }

        try:
            if self.mindset_path.exists():
                identity["user_mindset"] = self.mindset_path.read_text(encoding="utf-8")
            
            if self.soul_path.exists():
                identity["cct_soul"] = self.soul_path.read_text(encoding="utf-8")

        except Exception as e:
            logger.warning(f"[IDENTITY] Error reading identity files, using hardcoded DNA failover. Details: {e}")

        return identity

    def format_system_prefix(self, identity: Dict[str, str]) -> str:
        """
        Formats the identity layer into a unified system prompt segment.
        """
        soul = identity.get("cct_soul", SOVEREIGN_SOUL)
        mindset = identity.get("user_mindset", SOVEREIGN_MINDSET)

        return (
            "==========================================================\n"
            "CCT SOVEREIGN IDENTITY LAYER (DIGITAL SYMBIOSIS)\n"
            "==========================================================\n"
            f"{soul}\n\n"
            "----------------------------------------------------------\n"
            "USER ARCHITECTURAL DNA (MINDSET)\n"
            "----------------------------------------------------------\n"
            f"{mindset}\n"
            "==========================================================\n"
        )
