import sqlite3
import os
import re

DB_PATH = "cct_memory.db"
DOCS_ROOT = "docs/context-tree/Thinking-Patterns"

def run_final_migration():
    # 1. DB Updates
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Update thinking_patterns table
    cursor.execute("SELECT tp_id, data FROM thinking_patterns")
    patterns = cursor.fetchall()
    for old_id, data_str in patterns:
        new_id = old_id.replace("GS_", "TP_")
        new_data = data_str.replace("GS_", "TP_")
        cursor.execute("UPDATE thinking_patterns SET tp_id = ?, data = ? WHERE tp_id = ?", (new_id, new_data, old_id))
    
    # Update thoughts table
    cursor.execute("SELECT thought_id, data FROM thoughts")
    thoughts = cursor.fetchall()
    for tid, data_str in thoughts:
        if "GS_" in data_str:
            new_data = data_str.replace("GS_", "TP_")
            cursor.execute("UPDATE thoughts SET data = ? WHERE thought_id = ?", (new_data, tid))
            
    conn.commit()
    conn.close()
    print("[SUCCESS] Database IDs migrated GS_ -> TP_")

    # 2. File Updates
    if os.path.exists(DOCS_ROOT):
        for root, dirs, files in os.walk(DOCS_ROOT):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    # Content update
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    new_content = content.replace("GS_", "TP_")
                    
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    
                    # Filename update
                    if file.startswith("GS_"):
                        new_file_name = file.replace("GS_", "TP_")
                        new_file_path = os.path.join(root, new_file_name)
                        os.rename(file_path, new_file_path)
                        print(f"[FILE] Renamed {file} -> {new_file_name}")
    
    print("[SUCCESS] Documentation files migrated.")

if __name__ == "__main__":
    run_final_migration()
