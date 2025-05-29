import json
import logging
from pathlib import Path
import pandas as pd
import sqlite3
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = logging.getLogger(__name__)

# Define project root relative to this file (scraper.py in root)
# This helps if functions are called from other scripts (like webapp)
PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_FILE_PATH = PROJECT_ROOT / "config.json"
DB_FILE_PATH = PROJECT_ROOT / "job_listings.db"

try:
    import jobspy
except ImportError:
    logger.error("Failed to import 'jobspy'. Please ensure 'python-jobspy' is installed.", exc_info=True)
    # This will prevent the script from running if jobspy is not installed, which is intended.
    raise 

def load_scraper_config(config_path: Path = CONFIG_FILE_PATH) -> dict | None:
    """Loads the configuration file."""
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        logger.info(f"Scraper: Configuration loaded successfully from '{config_path}'.")
        return config_data
    except FileNotFoundError:
        logger.error(f"Scraper: Error - Configuration file '{config_path}' not found.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Scraper: Error - Could not decode JSON from '{config_path}'. Check its format.")
        return None
    except Exception as e:
        logger.error(f"Scraper: An unexpected error occurred while loading '{config_path}': {e}")
        return None

def get_scraper_db_connection(db_path: Path = DB_FILE_PATH) -> sqlite3.Connection | None:
    """Establishes a connection to the SQLite database for the scraper."""
    try:
        conn = sqlite3.connect(db_path)
        logger.info(f"Scraper: Successfully connected to database '{db_path}'.")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Scraper: Error connecting to database '{db_path}': {e}")
        return None

def store_jobs_in_db(jobs_df: pd.DataFrame, conn: sqlite3.Connection) -> tuple[int, int]:
    """Stores job listings from a DataFrame into the SQLite database."""
    if jobs_df is None or jobs_df.empty:
        logger.info("Scraper: No jobs to store in the database.")
        return 0, 0 # new_jobs_count, ignored_jobs_count

    cursor = conn.cursor()
    new_jobs_count = 0
    ignored_jobs_count = 0
    errors_count = 0

    for row in jobs_df.itertuples(index=False):
        job_id = getattr(row, 'job_url', None)
        if not job_id:
            logger.warning(f"Scraper: Skipping row due to missing job_url: {row}")
            errors_count +=1
            continue

        title = getattr(row, 'title', None)
        company = getattr(row, 'company', None)
        location = getattr(row, 'location', None)
        date_posted_raw = getattr(row, 'date_posted', None)
        date_posted = date_posted_raw 
        description_text = getattr(row, 'description', '')
        application_url = getattr(row, 'job_url_direct', getattr(row, 'apply_url', None))
        source = getattr(row, 'site', 'N/A')
        scraped_timestamp = datetime.now().isoformat()
        status = 'new'

        try:
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
            else:
                ignored_jobs_count += 1
        except sqlite3.Error as e:
            logger.error(f"Scraper: Error inserting job (ID: {job_id}): {e}")
            errors_count +=1
        except Exception as ex:
            logger.error(f"Scraper: General error processing job (ID: {job_id}): {ex}")
            errors_count +=1
            
    if errors_count > 0:
        logger.warning(f"Scraper: Encountered {errors_count} errors during job data processing/insertion.")
    
    conn.commit()
    logger.info(f"Scraper: Database update complete. New jobs added: {new_jobs_count}. Duplicate/ignored jobs: {ignored_jobs_count}.")
    return new_jobs_count, ignored_jobs_count


def fetch_raw_jobs(config: dict) -> pd.DataFrame | None:
    """Internal function to fetch jobs using JobSpy, separated for clarity."""
    if not config:
        logger.error("Scraper: Configuration data is missing for fetching.")
        return None
    
    job_prefs = config.get('job_preferences', {})
    personal_info = config.get('personal_info', {}) # Ensure personal_info is also fetched or default to {}

    desired_roles = job_prefs.get('desired_roles')
    target_locations = job_prefs.get('target_locations')

    if not desired_roles or not isinstance(desired_roles, list) or not desired_roles[0]:
        logger.error("Scraper: 'desired_roles' (list of non-empty strings) not found or format incorrect.")
        return None

    current_search_term = desired_roles[0] # Using only the first role
    current_location = "" 
    if target_locations and isinstance(target_locations, list) and target_locations[0]:
        current_location = target_locations[0] # Using only the first location

    country_indeed = "USA" 
    address = personal_info.get('address', {})
    country_field = address.get('country', address.get('Country'))
    if country_field and isinstance(country_field, str) and country_field.strip().upper() in ["USA", "US", "UNITED STATES"]:
        country_indeed = "USA"
    
    site_names = ['indeed', 'linkedin', 'zip_recruiter', 'glassdoor']
    
    logger.info(f"Scraper: Starting job search with JobSpy...")
    logger.info(f"  Sites: {site_names}")
    logger.info(f"  Search Term: {current_search_term}")
    logger.info(f"  Location: {current_location if current_location else 'Any'}")
    logger.info(f"  Country for Indeed: {country_indeed}")
    
    try:
        jobs_df = jobspy.scrape_jobs(
            site_name=site_names,
            search_term=current_search_term, 
            location=current_location,       
            country_indeed=country_indeed,
            results_wanted=10, 
            verbose_level=1, # 0 (silent), 1 (some logs), 2 (verbose)
        )
        
        if jobs_df is not None and not jobs_df.empty:
            logger.info(f"Scraper: Successfully fetched {len(jobs_df)} raw job listings.")
        elif jobs_df is not None and jobs_df.empty:
            logger.info(f"Scraper: No jobs found for term '{current_search_term}' in '{current_location}'.")
        else: # Should not happen if jobspy returns DataFrame or raises error
            logger.warning(f"Scraper: Job search returned None for term '{current_search_term}' in '{current_location}'.")
        return jobs_df if jobs_df is not None else pd.DataFrame()

    except Exception as e:
        logger.error(f"Scraper: An error occurred during job scraping with JobSpy: {e}", exc_info=True)
        return pd.DataFrame()


def run_scraping_and_storing(config_override: dict = None) -> dict:
    """
    Main callable function for the scraping process.
    Loads config, fetches jobs, and stores them in the database.
    Returns a summary of the operation.
    """
    summary = {
        "status": "started",
        "new_jobs_added": 0,
        "total_jobs_processed_from_fetch": 0,
        "duplicate_ignored_jobs": 0,
        "errors": []
    }

    logger.info("Scraper: === Starting run_scraping_and_storing ===")
    config = config_override if config_override else load_scraper_config()
    
    if not config:
        summary["status"] = "failed"
        summary["errors"].append("Configuration loading failed.")
        logger.error("Scraper: Configuration loading failed. Aborting scraping run.")
        return summary

    raw_jobs_df = fetch_raw_jobs(config)

    if raw_jobs_df is None or raw_jobs_df.empty:
        summary["status"] = "completed_no_data"
        logger.info("Scraper: No jobs fetched or an error occurred during fetching. Nothing to store.")
        if raw_jobs_df is None: # Indicates an error rather than just no jobs
             summary["errors"].append("Job fetching returned None, indicating an error.")
        return summary
    
    summary["total_jobs_processed_from_fetch"] = len(raw_jobs_df)

    conn = get_scraper_db_connection()
    if not conn:
        summary["status"] = "failed"
        summary["errors"].append("Database connection failed.")
        logger.error("Scraper: Database connection failed. Cannot store jobs.")
        return summary
    
    try:
        new_added, ignored = store_jobs_in_db(raw_jobs_df, conn)
        summary["new_jobs_added"] = new_added
        summary["duplicate_ignored_jobs"] = ignored
        summary["status"] = "success"
        logger.info("Scraper: Scraping and storing process completed successfully.")
    except Exception as e:
        summary["status"] = "failed"
        summary["errors"].append(f"An error occurred during storing jobs: {str(e)}")
        logger.error(f"Scraper: Error during storing jobs: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()
            logger.info("Scraper: Database connection closed.")
            
    logger.info(f"Scraper: === Finished run_scraping_and_storing. Summary: {summary} ===")
    return summary


if __name__ == "__main__":
    logger.info("Scraper script started for direct execution.")
    # Example of direct execution:
    # result_summary = run_scraping_and_storing()
    # logger.info(f"Direct execution summary: {result_summary}")
    
    # The old main block for just fetching and printing:
    config = load_scraper_config()
    if config:
        jobs_dataframe = fetch_raw_jobs(config) # Changed to fetch_raw_jobs
        if jobs_dataframe is not None and not jobs_dataframe.empty:
            logger.info(f"--- Total jobs fetched by scraper (direct run): {len(jobs_dataframe)} ---")
            logger.info("--- Sample of fetched jobs (first 5 rows, direct run): ---")
            with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
                print(jobs_dataframe.head().to_string())
        elif jobs_dataframe is not None and jobs_dataframe.empty:
            logger.info("No jobs were fetched (direct run).")
        else:
            logger.warning("Job fetching process did not complete successfully (direct run).")
    else:
        logger.error("Could not load configuration for direct run. Scraping aborted.")
        
    logger.info("Scraper script direct execution finished.")
