import sys
import os
from pathlib import Path

# Fix python path to include src
sys.path.append(str(Path("src").resolve()))

from utils.pricing import pricing_manager

model_id = "claude-3-5-sonnet-20240620"
print(f"Testing PricingManager for model: {model_id}")

# 1. Check dataset directory
print(f"Dataset Dir: {pricing_manager.dataset_dir}")
print(f"Exists: {pricing_manager.dataset_dir.exists()}")

# 2. Test lookup
pricing = pricing_manager._load_model_pricing(model_id)
print(f"Pricing Load: {'Success' if pricing else 'FAILED'}")
if pricing:
    print(f"Pricing Data keys: {list(pricing.keys())}")

# 3. Test calculation
costs = pricing_manager.calculate_costs(model_id, 1000, 1000)
print(f"Calculation Result: {costs}")
