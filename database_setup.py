import sqlite3
import datetime

def create_jobs_table(db_name="job_listings.db"):
    """
    Creates the 'jobs' table in the SQLite database if it doesn't already exist.

    Args:
        db_name (str): The name of the database file.
    """
    conn = None  # Initialize conn to None
    try:
        # Connect to the SQLite database (creates the file if it doesn't exist)
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Check if the table already exists
        cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'
        ''')
        table_exists = cursor.fetchone()

        if table_exists:
            print(f"Table 'jobs' already exists in '{db_name}'.")
        else:
            # Define the SQL CREATE TABLE statement
            # Using TEXT for dates/timestamps for simplicity with ISO formats.
            # UNIQUE constraint on job_url is important.
            create_table_sql = """
            CREATE TABLE jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                date_posted TEXT,
                description_text TEXT NOT NULL,
                job_url TEXT NOT NULL UNIQUE,
                application_url TEXT,
                source TEXT NOT NULL,
                scraped_timestamp TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'new' 
            );
            """
            # status examples: 'new', 'interested', 'applied', 'interviewing', 'offer', 'rejected', 'ignored'
            
            cursor.execute(create_table_sql)
            print(f"Table 'jobs' created successfully in '{db_name}'.")

        # Commit the changes
        conn.commit()

    except sqlite3.Error as e:
        print(f"SQLite error occurred: {e}")
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
