import os
import logging
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING

from src.core.models.user.identity import SOVEREIGN_MINDSET, SOVEREIGN_SOUL

if TYPE_CHECKING:
    from src.core.services.learning.hippocampus import HippocampusService

logger = logging.getLogger(__name__)

class UserIdentityService:
    """
    Manages the Identity Layer (Digital Symbiosis).
    Responsible for provisioning default assets and loading the identity context for sessions.
    
    DIGITAL TWIN ENHANCEMENT: Integrates with HippocampusService for
    dynamic identity learning and auto-build prompts based on user interactions.
    """

    def __init__(
        self, 
        identity_dir: str = "configs/identity",
        digital_hippocampus: Optional["HippocampusService"] = None
    ):
        self.identity_dir = Path(identity_dir)
        self.mindset_path = self.identity_dir / "mindset.md"
        self.soul_path = self.identity_dir / "soul.md"
        self.digital_hippocampus = digital_hippocampus

    def provision_assets(self) -> None:
        """
        Auto-seeds the identity directory with sovereign defaults if missing.
        Ensures a 'Zero-Config' experience for the user.
        """
        try:
            if not self.identity_dir.exists():
                logger.info(f"[IDENTITY] Creating directory: {self.identity_dir}")
                self.identity_dir.mkdir(parents=True, exist_ok=True)
                logger.debug(f"[IDENTITY] Directory created successfully with permissions: {oct(self.identity_dir.stat().st_mode)}")
            else:
                logger.debug(f"[IDENTITY] Directory already exists: {self.identity_dir}")

            if not self.mindset_path.exists():
                logger.info(f"[IDENTITY] Seeding sovereign mindset: {self.mindset_path}")
                self.mindset_path.write_text(SOVEREIGN_MINDSET, encoding="utf-8")
                logger.debug(f"[IDENTITY] Mindset file seeded successfully ({len(SOVEREIGN_MINDSET)} bytes)")
            else:
                logger.debug(f"[IDENTITY] Mindset file already exists: {self.mindset_path}")

            if not self.soul_path.exists():
                logger.info(f"[IDENTITY] Seeding CCT soul: {self.soul_path}")
                self.soul_path.write_text(SOVEREIGN_SOUL, encoding="utf-8")
                logger.debug(f"[IDENTITY] Soul file seeded successfully ({len(SOVEREIGN_SOUL)} bytes)")
            else:
                logger.debug(f"[IDENTITY] Soul file already exists: {self.soul_path}")

            logger.info(f"[IDENTITY] Provisioning complete - Tier 1 (Zero-Config) active")

        except PermissionError as e:
            logger.error(f"[IDENTITY] Permission denied during provisioning: {e}. Path: {self.identity_dir}")
            logger.warning("[IDENTITY] Falling back to Tier 2 (Hardcoded DNA) due to permission error")
        except OSError as e:
            logger.error(f"[IDENTITY] OS error during provisioning: {e}. Path: {self.identity_dir}")
            logger.warning("[IDENTITY] Falling back to Tier 2 (Hardcoded DNA) due to OS error")
        except Exception as e:
            logger.error(f"[IDENTITY] Unexpected error during provisioning: {e}", exc_info=True)
            logger.warning("[IDENTITY] Falling back to Tier 2 (Hardcoded DNA) due to unexpected error")
            # Non-fatal: we will fall back to constants during load_identity if files are missing

    def load_identity(self, use_learning: bool = True) -> Dict[str, str]:
        """
        Loads the mindset and soul context.
        Prioritizes files, falls back to hardcoded DNA if files are unreadable.
        
        DIGITAL TWIN: If DigitalHippocampus is available and use_learning=True,
        enhances the identity with learned patterns from user interactions.
        
        Args:
            use_learning: Whether to use DigitalHippocampus for dynamic identity enhancement
        
        Returns:
            Dict with 'user_mindset', 'cct_soul', and 'source' indicating the identity source
        """
        identity = {
            "user_mindset": SOVEREIGN_MINDSET,
            "cct_soul": SOVEREIGN_SOUL
        }

        mindset_loaded_from_file = False
        soul_loaded_from_file = False

        try:
            if self.mindset_path.exists():
                logger.debug(f"[IDENTITY] Loading mindset from file: {self.mindset_path}")
                identity["user_mindset"] = self.mindset_path.read_text(encoding="utf-8")
                mindset_loaded_from_file = True
                logger.info(f"[IDENTITY] Mindset loaded from file ({len(identity['user_mindset'])} bytes)")
            else:
                logger.warning(f"[IDENTITY] Mindset file not found: {self.mindset_path}. Using hardcoded Tier 2 fallback.")
            
            if self.soul_path.exists():
                logger.debug(f"[IDENTITY] Loading soul from file: {self.soul_path}")
                identity["cct_soul"] = self.soul_path.read_text(encoding="utf-8")
                soul_loaded_from_file = True
                logger.info(f"[IDENTITY] Soul loaded from file ({len(identity['cct_soul'])} bytes)")
            else:
                logger.warning(f"[IDENTITY] Soul file not found: {self.soul_path}. Using hardcoded Tier 2 fallback.")

            # Log overall tier status
            if mindset_loaded_from_file and soul_loaded_from_file:
                logger.info("[IDENTITY] Tier 1 (File-based) active for both mindset and soul")
                identity["source"] = "file"
            elif mindset_loaded_from_file or soul_loaded_from_file:
                logger.warning("[IDENTITY] Mixed tier: one component from file, one from hardcoded fallback")
                identity["source"] = "mixed"
            else:
                logger.warning("[IDENTITY] Tier 2 (Hardcoded DNA) active for both mindset and soul")
                identity["source"] = "hardcoded"

        except PermissionError as e:
            logger.error(f"[IDENTITY] Permission denied reading identity files: {e}", exc_info=True)
            logger.warning("[IDENTITY] Tier 2 (Hardcoded DNA) fallback activated due to permission error")
            identity["source"] = "hardcoded_permission_error"
        except UnicodeDecodeError as e:
            logger.error(f"[IDENTITY] Unicode decode error reading identity files: {e}", exc_info=True)
            logger.warning("[IDENTITY] Tier 2 (Hardcoded DNA) fallback activated due to encoding error")
            identity["source"] = "hardcoded_encoding_error"
        except OSError as e:
            logger.error(f"[IDENTITY] OS error reading identity files: {e}", exc_info=True)
            logger.warning("[IDENTITY] Tier 2 (Hardcoded DNA) fallback activated due to OS error")
            identity["source"] = "hardcoded_os_error"
        except Exception as e:
            logger.error(f"[IDENTITY] Unexpected error reading identity files: {e}", exc_info=True)
            logger.warning("[IDENTITY] Tier 2 (Hardcoded DNA) fallback activated due to unexpected error")
            identity["source"] = "hardcoded_error"

        # DIGITAL TWIN: Apply DigitalHippocampus learning if available
        if use_learning and self.digital_hippocampus:
            try:
                enhanced_identity = self.digital_hippocampus.get_enhanced_identity()
                if enhanced_identity.get("source") == "dynamic":
                    logger.info("[IDENTITY] Tier 4 (Dynamic Learning) active - using fully learned identity")
                    identity["user_mindset"] = enhanced_identity["user_mindset"]
                    identity["cct_soul"] = enhanced_identity["cct_soul"]
                    identity["source"] = "dynamic"
                elif enhanced_identity.get("source") == "hybrid":
                    logger.info("[IDENTITY] Tier 3.5 (Hybrid Learning) active - using static + learned identity")
                    identity["user_mindset"] = enhanced_identity["user_mindset"]
                    identity["cct_soul"] = enhanced_identity["cct_soul"]
                    identity["source"] = "hybrid"
                else:
                    logger.debug("[IDENTITY] DigitalHippocampus has insufficient data, using static identity")
            except Exception as e:
                logger.warning(f"[IDENTITY] Failed to apply DigitalHippocampus learning: {e}. Using static identity.")

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
