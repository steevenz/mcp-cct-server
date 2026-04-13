#!/usr/bin/env python
"""Debug script for pricing loading."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from pathlib import Path
from src.core.constants import DEFAULT_PRICING_PATH

print("=" * 60)
print("Debug Pricing Loading")
print("=" * 60)

print(f"\nDEFAULT_PRICING_PATH: {repr(DEFAULT_PRICING_PATH)}")

pricing_path = Path(DEFAULT_PRICING_PATH)
print(f"pricing_path: {pricing_path}")
print(f"pricing_path.exists(): {pricing_path.exists()}")
print(f"pricing_path.is_dir(): {pricing_path.is_dir()}")
print(f"pricing_path.absolute(): {pricing_path.absolute()}")

if pricing_path.exists() and pricing_path.is_dir():
    print("\nDirectory exists, listing JSON files:")
    json_files = list(pricing_path.glob('*.json'))
    print(f"Found {len(json_files)} JSON files:")
    
    registry = {}
    for f in json_files:
        print(f"\n  File: {f}")
        try:
            with open(f, 'r', encoding='utf-8') as file:
                data = json.load(file)
                model_id = data.get('model_id')
                print(f"    model_id: {model_id}")
                if model_id:
                    registry[model_id] = data
        except Exception as e:
            print(f"    Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nTotal registry size: {len(registry)}")
    print(f"Registry keys: {list(registry.keys())}")
else:
    print("\nDirectory does not exist!")
    
    # Try from current working directory
    cwd_path = Path.cwd() / DEFAULT_PRICING_PATH
    print(f"\nTrying from CWD: {cwd_path}")
    print(f"Exists: {cwd_path.exists()}")
    
    # Try from project root
    root_path = Path(__file__).parent.parent / DEFAULT_PRICING_PATH
    print(f"\nTrying from project root: {root_path}")
    print(f"Exists: {root_path.exists()}")

print("\n" + "=" * 60)
print("Debug complete")
print("=" * 60)
