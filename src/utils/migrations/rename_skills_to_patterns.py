import sqlite3
import json
import logging
import shutil
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TP_Migration")

DB_PATH = "cct_memory.db"
BACKUP_PATH = "cct_memory.db.bak"

def migrate():
    if not os.path.exists(DB_PATH):
        logger.error(f"Database {DB_PATH} not found. Nothing to migrate.")
        return

    # 1. Backup
    logger.info(f"💾 Creating backup: {BACKUP_PATH}")
    shutil.copy2(DB_PATH, BACKUP_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 2. Check if skills table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='skills'")
        if not cursor.fetchone():
            logger.info("Table 'skills' does not exist. Migration might have already run?")
        else:
            # 3. Rename Table
            logger.info("🔄 Renaming table 'skills' to 'thinking_patterns'...")
            cursor.execute("ALTER TABLE skills RENAME TO thinking_patterns")

            # 4. Rename Column
            logger.info("🔄 Renaming column 'skill_id' to 'tp_id'...")
            # SQLite 3.25.0+ supports RENAME COLUMN
            cursor.execute("ALTER TABLE thinking_patterns RENAME COLUMN skill_id TO tp_id")

        # 5. Update JSON data in thinking_patterns
        logger.info("🧹 Updating 'thinking_patterns' JSON blobs...")
        cursor.execute("SELECT tp_id, data FROM thinking_patterns")
        patterns = cursor.fetchall()
        for tp_id, data_json in patterns:
            data = json.loads(data_json)
            # Update internal naming
            # Replacing strings "skill" -> "thinking_pattern" (Case sensitive and insensitive)
            data_str = json.dumps(data)
            data_str = data_str.replace("Golden Skill", "Golden Thinking Pattern")
            data_str = data_str.replace("skill_id", "tp_id")
            cursor.execute("UPDATE thinking_patterns SET data = ? WHERE tp_id = ?", (data_str, tp_id))

        # 6. Update JSON data in thoughts table
        logger.info("🧹 Updating 'thoughts' JSON blobs (is_golden_skill field)...")
        cursor.execute("SELECT thought_id, data FROM thoughts")
        thoughts = cursor.fetchall()
        for t_id, data_json in thoughts:
            if "is_golden_skill" in data_json:
                updated_json = data_json.replace('"is_golden_skill":', '"is_thinking_pattern":')
                cursor.execute("UPDATE thoughts SET data = ? WHERE thought_id = ?", (updated_json, t_id))

        conn.commit()
        logger.info("✅ Migration Completed Successfully.")

    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Migration Failed: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
