import time
import json
import logging
import requests
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ForexService:
    """
    Automated Currency Exchange Rate Service.
    Fetches live data from Frankfurter API with persistent local caching.
    """
    API_URL = "https://api.frankfurter.app/latest?from=USD&to=IDR"
    CACHE_FILE = Path("database/metadata/forex_cache.json")
    CACHE_TTL = 86400  # 24 hours in seconds
    DEFAULT_RATE = 17095.0  # Safe fallback based on April 2026 baseline

    def __init__(self):
        self._ensure_metadata_dir()

    def _ensure_metadata_dir(self):
        """Ensures the metadata directory exists for caching."""
        self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    def get_usd_to_idr_rate(self) -> float:
        """
        Retrieves the USD/IDR rate using a Cache-Aside strategy.
        Returns the latest rate from API, Cache, or safe Fallback.
        """
        # 1. Try to load from Cache
        cache_data = self._load_cache()
        if cache_data:
            timestamp = cache_data.get("timestamp", 0)
            # Check if cache is still fresh
            if (time.time() - timestamp) < self.CACHE_TTL:
                logger.debug("Forex: Using fresh cached rate.")
                return cache_data.get("rate", self.DEFAULT_RATE)

        # 2. Cache is stale or missing -> Fetch from API
        try:
            logger.info("Forex: Fetching fresh rate from Frankfurter API...")
            response = requests.get(self.API_URL, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            rate = data.get("rates", {}).get("IDR")
            if rate:
                self._save_cache(rate)
                return float(rate)
        except Exception as e:
            logger.error(f"Forex: API fetch failed: {e}")

        # 3. Fallback to Stale Cache or Default
        if cache_data:
            logger.warning("Forex: API failed, falling back to stale cached rate.")
            return cache_data.get("rate", self.DEFAULT_RATE)

        logger.warning(f"Forex: All data sources failed. Using hardcoded fallback: {self.DEFAULT_RATE}")
        return self.DEFAULT_RATE

    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """Loads cached rate from disk."""
        if not self.CACHE_FILE.exists():
            return None
        try:
            with open(self.CACHE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Forex: Failed to read cache: {e}")
            return None

    def _save_cache(self, rate: float):
        """Saves fresh rate to disk with timestamp."""
        try:
            cache_data = {
                "rate": rate,
                "timestamp": time.time(),
                "date": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            with open(self.CACHE_FILE, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Forex: Failed to save cache: {e}")

class PricingManager:
    """
    Manages model pricing datasets and calculates cognitive costs.
    Uses 'Source of Truth' datasets from database/datasets/.
    """
    def __init__(self, dataset_dir: Optional[str] = None):
        # [FIX] Use absolute path resolution to ensure datasets are found regardless of CWD
        if dataset_dir:
            self.dataset_dir = Path(dataset_dir)
        else:
            project_root = Path(__file__).parent.parent.parent.resolve()
            self.dataset_dir = project_root / "database" / "datasets"
            
        self.pricing_cache: Dict[str, Dict[str, Any]] = {}
        self.forex = ForexService()
        logger.info(f"PricingManager initialized with dataset directory: {self.dataset_dir}")

    def _load_model_pricing(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Loads pricing JSON for a specific model_id with robust fallback logic."""
        # Standardize lookup key (lowercase and sanitized)
        lookup_id = model_id.lower().split(":")[0].replace("/", "-")
        
        # 0. Explicit Family Mapping (LLM-directed overrides)
        # Handle common model families to ensure stable mapping even with varied IDs
        family_mapping = {
            "gemini-3.5": "gemini-3.5-flash",
            "gemini-3": "gemini-3.5-flash",
            "gemini-2.0": "gemini-2.0-flash",
            "gemini-1.5": "gemini-1.5-flash",
            "gemini-pro": "gemini-1.5-pro",
            "claude-3.5-sonnet": "claude-3-5-sonnet",
            "claude-3.5-opus": "claude-3-opus",
            "claude-3.5": "claude-3-5-sonnet",
            "claude-3-sonnet": "claude-3-5-sonnet",
            "gpt-4o-mini": "gpt-4o-mini",
            "gpt-4o": "gpt-4o",
            "gpt-4-turbo": "gpt-4-turbo",
            "gpt-4": "gpt-4o"
        }

        
        for family, target in family_mapping.items():
            if lookup_id.startswith(family):
                lookup_id = target
                break

        if lookup_id in self.pricing_cache:
            return self.pricing_cache[lookup_id]
        
        # 1. Exact match attempt
        pricing_file = self.dataset_dir / f"{lookup_id}.json"
        
        # 2. Heuristic: If specific version not found, try base model
        if not pricing_file.exists():
            parts = lookup_id.split("-")
            for i in range(len(parts) - 1, 0, -1):
                trial_id = "-".join(parts[:i])
                trial_file = self.dataset_dir / f"{trial_id}.json"
                if trial_file.exists():
                    pricing_file = trial_file
                    break

        if not pricing_file.exists():
            logger.warning(f"No pricing dataset found for model: {model_id} (Resolved as: {lookup_id})")
            return None
            
        try:
            with open(pricing_file, "r") as f:
                data = json.load(f)
                self.pricing_cache[lookup_id] = data
                return data
        except Exception as e:
            logger.error(f"Error loading pricing file {pricing_file}: {e}")
            return None


    def calculate_costs(
        self, 
        model_id: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> Dict[str, float]:
        """
        Calculates granular costs in USD and IDR.
        Returns a dictionary with input, output, and total costs.
        """
        # [PESSIMISTIC FALLBACK] If specific model resolution fails, use the ai-common-model average
        if not pricing:
            logger.info(f"Using 'ai-common-model' fallback for: {model_id}")
            pricing = self._load_model_pricing("ai-common-model")
        
        # Default to 0 if pricing still not found (extreme safety)
        rates = {
            "input_1k": 0.0,
            "output_1k": 0.0
        }
        
        if pricing:
            # Support both per-1M schema (canonical) and legacy per-1K schema
            if "input_price_per_1m" in pricing:
                rates["input_1k"] = pricing["input_price_per_1m"] / 1000.0
                rates["output_1k"] = pricing["output_price_per_1m"] / 1000.0
            elif "pricing" in pricing:
                p_data = pricing["pricing"]
                rates["input_1k"] = p_data.get("input_1k", 0.0)
                rates["output_1k"] = p_data.get("output_1k", 0.0)

        # Calculate USD (Increased precision to 10 for micro-costs)
        in_cost_usd = (input_tokens / 1000.0) * rates["input_1k"]
        out_cost_usd = (output_tokens / 1000.0) * rates["output_1k"]
        total_usd = in_cost_usd + out_cost_usd

        # Calculate IDR (Dynamic via Forex Service, increased to 5 for micro-costs)
        usd_to_idr = self.forex.get_usd_to_idr_rate()
        in_cost_idr = in_cost_usd * usd_to_idr
        out_cost_idr = out_cost_usd * usd_to_idr
        total_idr = in_cost_idr + out_cost_idr

        return {
            "input_usd": round(in_cost_usd, 10),
            "output_usd": round(out_cost_usd, 10),
            "total_usd": round(total_usd, 10),
            "input_idr": round(in_cost_idr, 5),
            "output_idr": round(out_cost_idr, 5),
            "total_idr": round(total_idr, 5),
            # Audit field: exact rate used at calculation time
            "currency_rate_idr": usd_to_idr
        }

# Global instance for easier access
pricing_manager = PricingManager()
