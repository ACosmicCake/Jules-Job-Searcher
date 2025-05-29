import json
import logging
from pathlib import Path
import pandas as pd
import sqlite3
from datetime import datetime

# Attempt to import jobspy
try:
    import jobspy
except ImportError:
    logging.error("Failed to import 'jobspy'. Please ensure 'python-jobspy' is installed.", exc_info=True)
    raise

# 1. Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 2. Load Configuration Function
def load_config(config_path="config.json"):
    """Loads the configuration file."""
    try:
        config_file = Path(config_path)
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        logging.info(f"Configuration loaded successfully from '{config_path}'.")
        return config_data
    except FileNotFoundError:
        logging.error(f"Error: Configuration file '{config_path}' not found.")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error: Could not decode JSON from '{config_path}'. Check its format.")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading '{config_path}': {e}")
        return None

# Database Connection Function
def get_db_connection(db_name="job_listings.db"):
    """Establishes a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(db_name)
        logging.info(f"Successfully connected to database '{db_name}'.")
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database '{db_name}': {e}")
        return None

# Data Transformation and Insertion Function
def store_jobs_in_db(jobs_df, conn):
    """Stores job listings from a DataFrame into the SQLite database."""
    if jobs_df is None or jobs_df.empty:
        logging.info("No jobs to store in the database.")
        return 0

    cursor = conn.cursor()
    new_jobs_count = 0
    ignored_jobs_count = 0

    for row in jobs_df.itertuples(index=False):
        # Use job_url as the primary key 'id' in the database
        # The database schema has 'id TEXT PRIMARY KEY' and 'job_url TEXT UNIQUE'.
        # We will use job_url for the 'id' column. The 'job_url' column in DB is then redundant if 'id' holds the URL.
        # For this implementation, we'll populate 'id' with job_url and also job_url column for clarity,
        # though 'INSERT OR IGNORE' will primarily use the 'id' (PK) for conflict resolution.
        
        job_id = getattr(row, 'job_url', None)
        if not job_id:
            logging.warning(f"Skipping row due to missing job_url: {row}")
            continue

        # Map DataFrame columns to database columns
        title = getattr(row, 'title', None)
        company = getattr(row, 'company', None)
        location = getattr(row, 'location', None)
        
        # Date posted: JobSpy's 'date_posted' field. Need to ensure it's in 'YYYY-MM-DD' or handle conversion.
        # For now, assume it's a string that SQLite can store.
        date_posted_raw = getattr(row, 'date_posted', None) # Or 'timestamp' / 'date' depending on JobSpy output
        date_posted = date_posted_raw # Add formatting if needed: e.g. pd.to_datetime(date_posted_raw).strftime('%Y-%m-%d') if it's a datetime object

        description_text = getattr(row, 'description', '') # Ensure not None
        # job_url is already job_id
        application_url = getattr(row, 'job_url_direct', getattr(row, 'apply_url', None)) # Prefer 'job_url_direct' if available
        source = getattr(row, 'site', 'N/A') # 'site' column from JobSpy
        scraped_timestamp = datetime.now().isoformat()
        status = 'new' # Default status

        try:
            # 'id' column in DB stores the job_url.
            # The 'job_url' column in the DB schema becomes redundant if id is the url,
            # but we'll populate it anyway as per current schema.
            cursor.execute("""
                INSERT OR IGNORE INTO jobs (
                    id, title, company, location, date_posted, 
                    description_text, job_url, application_url, source, 
                    scraped_timestamp, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job_id, title, company, location, date_posted, 
                  description_text, job_id, application_url, source, 
                  scraped_timestamp, status))
            
            if cursor.rowcount > 0:
                new_jobs_count += 1
                logging.debug(f"Inserted new job: {title} at {company}")
            else:
                ignored_jobs_count += 1
                logging.debug(f"Ignored duplicate job: {title} at {company}")

        except sqlite3.Error as e:
            logging.error(f"Error inserting job (ID: {job_id}): {e} - Row data: {row}")
        except Exception as ex: # Catch any other potential errors during data mapping/insertion
            logging.error(f"General error processing job (ID: {job_id}): {ex} - Row data: {row}")


    conn.commit()
    logging.info(f"Database update complete. New jobs added: {new_jobs_count}. Duplicate/ignored jobs: {ignored_jobs_count}.")
    return new_jobs_count


# Main Scraping Function (modified)
def fetch_jobs(config):
    """Fetches jobs and stores them in the database."""
    if not config:
        logging.error("Configuration data is missing.")
        return None # Return None to indicate failure to fetch/process
    
    job_prefs = config.get('job_preferences')
    personal_info = config.get('personal_info')

    if not job_prefs:
        logging.error("Job preferences not found in configuration.")
        return None

    desired_roles = job_prefs.get('desired_roles')
    target_locations = job_prefs.get('target_locations')

    if not desired_roles or not isinstance(desired_roles, list) or not all(isinstance(role, str) for role in desired_roles) or not desired_roles:
        logging.error("No 'desired_roles' (list of non-empty strings) found in job_preferences or format is incorrect.")
        return None

    current_search_term = desired_roles[0]
    current_location = "" 
    if target_locations and isinstance(target_locations, list) and all(isinstance(loc, str) for loc in target_locations) and target_locations:
        current_location = target_locations[0]

    country_indeed = "USA" 
    if personal_info and isinstance(personal_info, dict):
        address = personal_info.get('address')
        if address and isinstance(address, dict):
            country_field = address.get('country', address.get('Country')) 
            if country_field and isinstance(country_field, str) and country_field.strip():
                if country_field.upper() in ["USA", "US", "UNITED STATES"]:
                    country_indeed = "USA"
    
    site_names = ['indeed', 'linkedin', 'zip_recruiter', 'glassdoor']
    
    logging.info(f"Starting job search with JobSpy...")
    logging.info(f"  Sites: {site_names}")
    logging.info(f"  Search Term (Role): {current_search_term}")
    logging.info(f"  Location: {current_location if current_location else 'Any'}")
    logging.info(f"  Country for Indeed: {country_indeed}")
    
    jobs_df = None # Initialize jobs_df
    try:
        jobs_df = jobspy.scrape_jobs(
            site_name=site_names,
            search_term=current_search_term, 
            location=current_location,       
            country_indeed=country_indeed,
            results_wanted=10, # Increased slightly to get more potential new entries
            verbose_level=1, 
        )
        
        if jobs_df is not None and not jobs_df.empty:
            logging.info(f"Successfully fetched {len(jobs_df)} jobs for term '{current_search_term}' in '{current_location}'.")
        elif jobs_df is not None and jobs_df.empty:
            logging.info(f"No jobs found for term '{current_search_term}' in '{current_location}'.")
            return pd.DataFrame() # Return empty DataFrame, no need to store
        else:
            logging.warning(f"Job search returned None for term '{current_search_term}' in '{current_location}'.")
            return pd.DataFrame() # Return empty DataFrame

    except Exception as e:
        logging.error(f"An error occurred during job scraping with JobSpy: {e}", exc_info=True)
        return pd.DataFrame() # Return empty DataFrame on error

    # --- Database Interaction ---
    if jobs_df is not None and not jobs_df.empty:
        conn = get_db_connection()
        if conn:
            try:
                store_jobs_in_db(jobs_df, conn)
            finally:
                conn.close()
                logging.info("Database connection closed.")
        else:
            logging.error("Failed to connect to the database. Jobs not stored.")
    
    return jobs_df # Return the fetched DataFrame


# Main Execution Block
if __name__ == "__main__":
    logging.info("Job Scraper script started.")
    
    config_data = load_config()
    
    if config_data:
        fetched_jobs_dataframe = fetch_jobs(config_data) # Renamed for clarity
        
        if fetched_jobs_dataframe is not None and not fetched_jobs_dataframe.empty:
            logging.info(f"--- Total jobs fetched by scraper: {len(fetched_jobs_dataframe)} ---")
            logging.info("--- Sample of fetched jobs (first 5 rows): ---")
            with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
                print(fetched_jobs_dataframe.head().to_string())

            logging.info("\n--- Example Job Details (first 3 jobs from fetch): ---")
            for i, row in fetched_jobs_dataframe.head(3).iterrows():
                title = row.get('title', 'N/A')
                company = row.get('company', 'N/A')
                source = row.get('site', 'N/A') 
                job_url_val = row.get('job_url', 'N/A')
                print(f"  Title: {title}\n  Company: {company}\n  Source: {source}\n  URL: {job_url_val}\n---")
        
        elif fetched_jobs_dataframe is not None and fetched_jobs_dataframe.empty:
            logging.info("No jobs were fetched or found matching your criteria.")
        else: # This case implies fetch_jobs returned None, meaning a pre-scraping error occurred.
            logging.warning("Job fetching process did not complete successfully or returned None.")
    else:
        logging.error("Could not load configuration. Job scraping aborted.")
        
    logging.info("Job Scraper script finished.")
