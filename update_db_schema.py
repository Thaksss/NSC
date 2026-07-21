import os
import psycopg2

def migrate():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set")
        return
        
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Add profile_image to users table if it doesn't exist
        try:
            cur.execute("ALTER TABLE users ADD COLUMN profile_image TEXT DEFAULT 'default_profile.png'")
            print("Added profile_image column to users")
        except psycopg2.errors.DuplicateColumn:
            print("profile_image column already exists")
            conn.rollback() # Rollback the failed transaction block
        
        # Ensure we are in a clean transaction state
        conn.commit()
        
        # Create daily_quests table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_quests (
                id SERIAL PRIMARY KEY,
                username TEXT NOT NULL,
                date DATE NOT NULL,
                quest1_id INTEGER NOT NULL,
                quest1_progress INTEGER DEFAULT 0,
                quest1_completed BOOLEAN DEFAULT FALSE,
                quest2_id INTEGER NOT NULL,
                quest2_progress INTEGER DEFAULT 0,
                quest2_completed BOOLEAN DEFAULT FALSE
            )
        """)
        
        # Create an index on username and date for fast lookups
        try:
            cur.execute("CREATE INDEX idx_daily_quests_user_date ON daily_quests(username, date)")
        except psycopg2.errors.DuplicateTable:
            pass # Index already exists
            conn.rollback()
        except psycopg2.errors.DuplicateObject:
            pass
            conn.rollback()
            
        conn.commit()
        print("Migration successful")
        
    except Exception as e:
        print(f"Error during migration: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate()
