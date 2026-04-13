import sys
import os
sys.path.append(os.getcwd())
from src.core.models.enums import SessionStatus
print(f"Status: {SessionStatus.ACTIVE}")
print(f"Type: {type(SessionStatus.ACTIVE)}")
print(f"Value: {SessionStatus.ACTIVE.value}")
s = "active"
print(f"Has value: {hasattr(s, 'value')}")
