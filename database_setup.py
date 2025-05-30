import sqlite3
import datetime

def create_jobs_table(db_name="job_listings.db"):
    """
    Creates the 'jobs' table in the SQLite database if it doesn't already exist.
    The table schema includes columns for job details and metadata.
    Indexes are created for efficient querying.

    Args:
        db_name (str): The name of the database file. Defaults to "job_listings.db".
    """
    conn = None  # Initialize conn to None
    try:
        # Connect to the SQLite database (creates the file if it doesn't exist)
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Check if the table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        table_exists = cursor.fetchone()

        if table_exists:
            print(f"Table 'jobs' already exists in '{db_name}'. No schema changes applied if it exists.")
        else:
            # Define the SQL CREATE TABLE statement
            # Using IF NOT EXISTS for robustness, though the outer check handles it too.
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_site_id TEXT UNIQUE,
                title TEXT,
                company TEXT,
                location TEXT,
                date_posted TEXT,
                job_url TEXT UNIQUE,
                description_text TEXT,
                source TEXT,
                emails TEXT,
                salary_text TEXT,
                job_type TEXT,
                scraped_timestamp TEXT,
                status TEXT DEFAULT 'new'
            );
            """
            cursor.execute(create_table_sql)
            print(f"Table 'jobs' created successfully (or already existed with IF NOT EXISTS) in '{db_name}'.")

            # Create indexes IF NOT EXISTS
            print("Creating indexes (if they don't exist)...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_site_id ON jobs (job_site_id);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_url ON jobs (job_url);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_date_posted ON jobs (date_posted);")
            print("Indexes created successfully (or already existed).")

        # Commit the changes, important even if only creating indexes on existing table
        conn.commit()

    except sqlite3.Error as e:
        print(f"SQLite error in create_jobs_table: {e}")
    finally:
        # Close the connection
        if conn:
            conn.close()
            # print(f"Database connection to '{db_name}' closed.")

if __name__ == "__main__":
    print("Setting up database...")
    # Get current timestamp for scraped_timestamp (example, not used in table creation itself)
    # current_time = datetime.datetime.now().isoformat()
    create_jobs_table()
    print("Database setup process finished.")
