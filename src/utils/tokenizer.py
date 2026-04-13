import re
import logging
from typing import Optional, List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Try to import tiktoken for high-precision counting
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False
    logger.warning("tiktoken not found. Falling back to heuristic token counting.")

# Heuristic BPE-style regex for better native counting
# This handles whitespace leading tokens and punctuation better than simple word regex.
_HEURISTIC_BPE_PATTERN = re.compile(r"""'s|'t|'re|'ve|'m|'ll|'d| ?[a-zA-Z\d]+| ?[^\s\w]+|\s+(?!\S)|\s+""", re.UNICODE)

class TokenEncoderFactory:
    """
    Factory for model-aware token encoders.
    Provides tiktoken encoders for OpenAI/Claude and heuristic fallbacks for others.
    """
    _encoders: Dict[str, Any] = {}

    @classmethod
    def get_encoder(cls, model_id: str = "claude-3-5-sonnet-20240620"):
        """Gets or creates an encoder for the specified model."""
        if model_id in cls._encoders:
            return cls._encoders[model_id]

        encoder = None
        if HAS_TIKTOKEN:
            try:
                # Map common models to tiktoken encodings
                if "gpt-4o" in model_id:
                    encoder = tiktoken.get_encoding("o200k_base")
                elif "gpt-4" in model_id or "gpt-3.5" in model_id or "claude-3" in model_id:
                    # Claude-3 uses a proprietary tokenizer, but cl100k_base is the closest open equivalent
                    encoder = tiktoken.get_encoding("cl100k_base")
                else:
                    # Default to cl100k_base as it's the most common modern standard
                    encoder = tiktoken.get_encoding("cl100k_base")
            except Exception as e:
                logger.debug(f"Tiktoken failed to load encoder for {model_id}: {e}")

        if not encoder:
            encoder = HeuristicEncoder(model_id)

        cls._encoders[model_id] = encoder
        return encoder

class HeuristicEncoder:
    """Fallback encoder that uses a sophisticated regex to estimate tokens."""
    def __init__(self, model_id: str):
        self.model_id = model_id

    def encode(self, text: str) -> List[int]:
        """Simple encoding mock returning dummy IDs based on regex matches."""
        # We don't need real IDs, just the count for most purposes
        # But we return a list to match tiktoken's interface
        matches = _HEURISTIC_BPE_PATTERN.findall(text)
        return [0] * len(matches)

    def count(self, text: str) -> int:
        """Efficiently count tokens without full list generation."""
        return len(_HEURISTIC_BPE_PATTERN.findall(text))

def count_tokens(text: str, model_id: str = "claude-3-5-sonnet-20240620") -> int:
    """
    Main entry point for token counting.
    Automatically uses best available method for the specific model.
    """
    if not text:
        return 0
        
    try:
        encoder = TokenEncoderFactory.get_encoder(model_id)
        if hasattr(encoder, 'count'):
            return encoder.count(text)
        return len(encoder.encode(text))
    except Exception as e:
        logger.error(f"Token count failed for model {model_id}: {e}")
        # Absolute worst case fallback: length-based approximation (4 chars per token)
        return max(1, len(text) // 4)
