import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.main import bootstrap

def test_bootstrap():
    print("Testing CCT Bootstrap process...")
    try:
        components = bootstrap()
        print("[OK] Bootstrap successful!")
        print(f"Components initialized: {list(components.keys())}")
        
        orchestrator = components["orchestrator"]
        print(f"[OK] Orchestrator initialized: {type(orchestrator).__name__}")
        
        # Verify uninitialized router bug fix
        if hasattr(orchestrator, 'router') and orchestrator.router is not None:
             print("[OK] Orchestrator router initialized.")
        else:
             print("[FIL] Orchestrator router MISSING.")
             
        # Verify identity service integration
        if hasattr(orchestrator.identity, 'digital_hippocampus') and orchestrator.identity.digital_hippocampus is not None:
            print("[OK] Identity service connected to Digital Hippocampus.")
        else:
            print("[FAIL] Identity service NOT connected to Digital Hippocampus.")
            
        print("\nVerification process complete.")
    except Exception as e:
        print(f"[FAIL] Bootstrap failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bootstrap()
