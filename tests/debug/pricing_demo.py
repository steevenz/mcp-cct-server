#!/usr/bin/env python
"""Test script for per-model pricing calculation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.harness import TokenHarness

def test_pricing():
    print("=" * 60)
    print("TokenHarness Per-Model Pricing Test")
    print("=" * 60)
    
    harness = TokenHarness()
    
    print(f"\nLoaded {len(harness.registry)} models from database/datasets/")
    print(f"Models: {list(harness.registry.keys())}")
    
    print("\n" + "-" * 60)
    print("Cost Calculations (1000 prompt + 500 completion tokens):")
    print("-" * 60)
    
    test_cases = [
        ('claude-3-5-sonnet-20240620', 1000, 500),
        ('claude-3-opus-20240229', 1000, 500),
        ('claude-3-haiku-20240307', 1000, 500),
        ('gpt-4o', 1000, 500),
        ('gpt-4-turbo', 1000, 500),
        ('gpt-3.5-turbo-0125', 1000, 500),
    ]
    
    for model_id, prompt_tokens, completion_tokens in test_cases:
        cost = harness.calculate_cost(model_id, prompt_tokens, completion_tokens)
        is_supported = harness.is_model_supported(model_id)
        pricing = harness.get_model_pricing(model_id)
        name = pricing.get('name', 'Unknown')
        
        print(f"  {model_id}")
        print(f"    Name: {name}")
        print(f"    Cost: ${cost:.6f} USD")
        print(f"    Supported: {is_supported}")
        print()
    
    # Test partial matching
    print("-" * 60)
    print("Partial Model ID Lookup Test:")
    print("-" * 60)
    
    partial_tests = [
        'claude-3-5-sonnet',
        'gpt-4o',
        'claude-3-opus',
    ]
    
    for partial in partial_tests:
        pricing = harness.get_model_pricing(partial)
        if pricing:
            print(f"  '{partial}' -> {pricing.get('name', 'Unknown')}")
        else:
            print(f"  '{partial}' -> Not found")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_pricing()
