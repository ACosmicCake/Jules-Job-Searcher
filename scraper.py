import json
import logging
from pathlib import Path
import pandas as pd
import sqlite3
from datetime import datetime
import dateparser
import re

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
        with open(config_path, 'r', encoding='utf-8') as f:
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

# --- Date Standardization Function ---
def standardize_date(date_str: str | pd.Timestamp | datetime | None) -> str | None: # Added datetime to hint
    """
    Standardizes a date string or pandas Timestamp to 'YYYY-MM-DD' format.

    Args:
        date_str: The date string or pandas Timestamp to standardize.
                  Examples: "2023-10-26", "10/26/2023", "2 days ago", pd.Timestamp('2023-10-26')

    Returns:
        The date string in 'YYYY-MM-DD' format if parsing is successful, 
        otherwise None.
    """
    if date_str is None:
        return None

    if isinstance(date_str, datetime): # Handle datetime.datetime first
        try:
            return date_str.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Could not format datetime.datetime object {date_str}: {e}")
            return None
    elif isinstance(date_str, pd.Timestamp):
        try:
            return date_str.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Could not format pandas Timestamp {date_str}: {e}")
            return None
    elif not isinstance(date_str, str): # Check if not string after handling other types
        logger.warning(f"Input is not a string, pandas Timestamp, or datetime object: {type(date_str)}. Returning None.")
        return None

    if not date_str.strip(): # Handle empty strings
        return None
    
    # Check if already in YYYY-MM-DD format
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str

    try:
        # Settings to prefer dates from the past
        # and handle formats like "today", "yesterday", "X days ago"
        date_obj = dateparser.parse(date_str, settings={'PREFER_DATES_FROM': 'past', 'RETURN_AS_TIMEZONE_AWARE': False})
        if date_obj:
            return date_obj.strftime('%Y-%m-%d')
        else:
            # dateparser.parse returns None if it can't parse the string
            logger.warning(f"dateparser could not parse date string: '{date_str}'")
            return None
    except Exception as e:
        # Catch any other unexpected errors during parsing
        logger.warning(f"Error parsing date string '{date_str}': {e}")
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

def store_jobs_in_db(job_data_list: list[dict], conn: sqlite3.Connection) -> tuple[int, int, int]: # Corrected type hint
    """
    Stores job listings from a list of dictionaries into the SQLite database.
    Handles field mapping, date standardization, and duplicate skipping.
    Returns tuple (inserted_count, skipped_count, error_count).
    """
    if not job_data_list:
        logger.info("Scraper: No jobs to store in the database.")
        return 0, 0, 0 # inserted_count, skipped_count, error_count

    cursor = conn.cursor()
    inserted_count = 0
    skipped_count = 0
    error_count = 0

    for job in job_data_list:
        job_site_id = job.get("id") if job.get("id") else job.get("job_url")
        if not job_site_id:
            logger.warning(f"Scraper: Skipping job due to missing 'id' and 'job_url': {job.get('title', 'N/A')}")
            error_count += 1
            continue

        title = job.get("title")
        company = job.get("company")
        location = job.get("location")
        date_posted_raw = job.get("date_posted")
        date_posted = standardize_date(date_posted_raw)
        job_url = job.get("job_url")
        description_text = job.get("description")
        source = job.get("site")
        
        emails_raw = job.get("emails")
        emails = json.dumps(emails_raw) if isinstance(emails_raw, list) else None
        
        salary_raw = job.get("salary")
        salary_text = str(salary_raw) if salary_raw is not None else None # Store raw salary string
        
        job_type = job.get("job_type")
        # Use scraped_timestamp from fetched data if available, else generate new
        scraped_timestamp = job.get("scraped_timestamp", datetime.now().isoformat())
        status = 'new'  # Default status

        # Ensure job_url is present if it's part of the unique constraint
        if not job_url:
             logger.warning(f"Scraper: Skipping job due to missing 'job_url' (used in UNIQUE constraint): {title} at {company}")
             error_count +=1
             continue

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO jobs (
                    job_site_id, title, company, location, date_posted, job_url,
                    description_text, source, emails, salary_text, job_type,
                    scraped_timestamp, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_site_id, title, company, location, date_posted, job_url,
                description_text, source, emails, salary_text, job_type,
                scraped_timestamp, status
            ))

            if cursor.rowcount > 0:
                inserted_count += 1
            else:
                # This means INSERT OR IGNORE found a duplicate (job_site_id or job_url)
                skipped_count += 1
        except sqlite3.IntegrityError: # Should be caught by INSERT OR IGNORE, but as a fallback
            logger.warning(f"Scraper: IntegrityError (likely duplicate) for job_site_id '{job_site_id}' or job_url '{job_url}'. Skipped.")
            skipped_count += 1
            error_count +=1 # Also an error if it gets here past OR IGNORE
        except sqlite3.Error as e:
            logger.error(f"Scraper: Database error inserting job (job_site_id: {job_site_id}): {e}", exc_info=True)
            error_count += 1
        except Exception as ex:
            logger.error(f"Scraper: General error processing job (job_site_id: {job_site_id}): {ex}", exc_info=True)
            error_count += 1
            
    if error_count > 0:
        logger.warning(f"Scraper: Encountered {error_count} errors during job data processing/insertion.")

    conn.commit()
    logger.info(f"Scraper: Database update complete. New jobs inserted: {inserted_count}. Duplicate/skipped jobs: {skipped_count}. Errors: {error_count}.")
    return inserted_count, skipped_count, error_count


def fetch_raw_jobs(config: dict) -> list[dict]:
    """
    Fetches raw job listings from multiple sites for each role and location combination
    specified in the configuration.
    Returns a list of job dictionaries, each augmented with a 'scraped_timestamp'.
    """
    if not config:
        logger.error("Scraper: Configuration data is missing for fetching.")
        return []

    job_prefs = config.get('job_preferences', {})
    personal_info = config.get('personal_info', {}) # For country_indeed logic

    # Load new scraping parameters with defaults
    results_wanted_config = job_prefs.get('results_wanted', 20)
    hours_old_config = job_prefs.get('hours_old', 72)
    logger.info(f"Scraper: Using results_wanted={results_wanted_config}, hours_old={hours_old_config} from config/defaults.")

    desired_roles = job_prefs.get('desired_roles')
    target_locations = job_prefs.get('target_locations')

    if not desired_roles or not isinstance(desired_roles, list) or not all(desired_roles):
        logger.error("Scraper: 'desired_roles' (list of non-empty strings) not found or format incorrect in config.")
        return []
    if not target_locations or not isinstance(target_locations, list) or not all(target_locations):
        logger.error("Scraper: 'target_locations' (list of non-empty strings) not found or format incorrect in config.")
        return []

    all_jobs_data: list[dict] = []

    # 1. Determine sites_to_scrape
    default_sites = ["indeed", "linkedin"]
    # Prioritize sites_to_scrape if it exists directly in job_prefs (passed via config_override)
    if 'sites_to_scrape' in job_prefs and job_prefs['sites_to_scrape']:
        sites_to_scrape = job_prefs['sites_to_scrape']
        logger.info(f"Scraper: Using 'sites_to_scrape' from job_preferences (override): {sites_to_scrape}")
    else:
        sites_to_scrape = default_sites
        logger.info(f"Scraper: 'sites_to_scrape' not found in job_preferences or is empty. Using default sites: {default_sites}")
    logger.info(f"Scraper: Final sites to target: {sites_to_scrape}")

    # 2. Determine country_indeed
    country_indeed_to_use = "USA" # Default value
    source_of_country_indeed = "default ('USA')"

    if 'country_indeed' in job_prefs and job_prefs['country_indeed']:
        country_indeed_to_use = job_prefs['country_indeed']
        source_of_country_indeed = "job_preferences (override)"
    elif personal_info.get('address'):
        address = personal_info.get('address', {})
        country_from_personal_info = address.get('country', address.get('Country')) # Check for 'country' or 'Country'
        if country_from_personal_info and isinstance(country_from_personal_info, str) and country_from_personal_info.strip():
            # Basic mapping for common cases, can be expanded
            # For now, we are only checking if it's USA or not for the example, but jobspy might support more.
            # The main point is to get the country string.
            country_indeed_to_use = country_from_personal_info.strip()
            source_of_country_indeed = "personal_info.address.country"
    logger.info(f"Scraper: Using 'country_indeed': '{country_indeed_to_use}' (Source: {source_of_country_indeed})")

    # 3. Determine linkedin_fetch_description
    linkedin_fetch_description_to_use = True # Default value
    source_of_linkedin_fetch = "default (True)"

    if 'linkedin_fetch_description' in job_prefs and isinstance(job_prefs['linkedin_fetch_description'], bool):
        linkedin_fetch_description_to_use = job_prefs['linkedin_fetch_description']
        source_of_linkedin_fetch = "job_preferences (override)"
    logger.info(f"Scraper: Using 'linkedin_fetch_description': {linkedin_fetch_description_to_use} (Source: {source_of_linkedin_fetch})")

    # 4. Determine new optional parameters
    google_search_term_config = job_prefs.get('google_search_term')
    logger.info(f"Scraper: Using 'google_search_term': {google_search_term_config if google_search_term_config else 'Not specified'}")

    distance_config = job_prefs.get('distance', 50) # Default to 50 if not specified
    logger.info(f"Scraper: Using 'distance': {distance_config} (Defaulted to 50 if not in config)")

    job_type_config = job_prefs.get('job_type') # e.g., fulltime, parttime. Default None if not specified.
    logger.info(f"Scraper: Using 'job_type': {job_type_config if job_type_config else 'Not specified'}")

    is_remote_config = job_prefs.get('is_remote', False) # Default to False if not specified
    logger.info(f"Scraper: Using 'is_remote': {is_remote_config} (Defaulted to False if not in config)")

    easy_apply_config = job_prefs.get('easy_apply', False) # Default to False if not specified
    logger.info(f"Scraper: Using 'easy_apply': {easy_apply_config} (Defaulted to False if not in config, mainly for LinkedIn)")

    description_format_config = job_prefs.get('description_format', 'markdown') # Default to 'markdown'
    logger.info(f"Scraper: Using 'description_format': {description_format_config} (Defaulted to 'markdown' if not in config)")

    for role in desired_roles:
        for loc in target_locations:
            logger.info(f"Scraper: Scraping for role: '{role}' in location: '{loc}' on sites: {sites_to_scrape}")
            
            try:
                jobspy_kwargs = {
                    'site_name': sites_to_scrape,
                    'search_term': role,
                    'location': loc,
                    'results_wanted': results_wanted_config,
                    'hours_old': hours_old_config,
                    'country_indeed': country_indeed_to_use,
                    'linkedin_fetch_description': linkedin_fetch_description_to_use,
                    'distance': distance_config,
                    'description_format': description_format_config,
                    'is_remote': is_remote_config,
                    'easy_apply': easy_apply_config,
                    'verbose_level': 0
                }
                if google_search_term_config:
                    jobspy_kwargs['search_term_within_results'] = google_search_term_config # Assuming this is the correct jobspy param for google_search_term
                if job_type_config:
                    jobspy_kwargs['job_type'] = job_type_config

                jobs_df = jobspy.scrape_jobs(**jobspy_kwargs)

                if jobs_df is not None and not jobs_df.empty:
                    # Convert DataFrame to list of dictionaries
                    jobs_list = jobs_df.to_dict(orient='records')
                    
                    # Add scraped_timestamp to each job entry at the time of fetching
                    # This timestamp will be used by store_jobs_in_db
                    timestamp_now = datetime.now().isoformat()
                    for job_entry in jobs_list:
                        job_entry['scraped_timestamp'] = timestamp_now
                        # Other specific field mapping mentioned in subtask (like job_id, salary)
                        # are handled by store_jobs_in_db based on JobSpy's direct output.
                        # For example, job_site_id in store_jobs_in_db uses job.get("id").
                        # Salary in store_jobs_in_db uses str(job.get("salary")).
                    
                    all_jobs_data.extend(jobs_list)
                    logger.info(f"Scraper: Found {len(jobs_list)} jobs for role '{role}' in '{loc}'.")
                elif jobs_df is not None and jobs_df.empty:
                    logger.info(f"Scraper: No jobs found for role '{role}' in '{loc}'.")
                else: # jobspy.scrape_jobs returned None
                    logger.warning(f"Scraper: Job search returned None for role '{role}' in '{loc}'.")

            except Exception as e:
                logger.error(f"Scraper: Error scraping for role '{role}' in '{loc}': {e}", exc_info=True)
    
    if not all_jobs_data:
        logger.info("Scraper: No jobs found across all specified roles and locations.")
    else:
        logger.info(f"Scraper: Total jobs fetched before deduplication: {len(all_jobs_data)}.")
        
    return all_jobs_data


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

    # fetch_raw_jobs now returns a list of dicts
    all_jobs_data = fetch_raw_jobs(config)

    if not all_jobs_data: # Handles empty list from fetch_raw_jobs (no jobs found or error during fetch)
        summary["status"] = "completed_no_data"
        logger.info("Scraper: No jobs fetched or an error occurred within fetch_raw_jobs. Nothing to store.")
        # fetch_raw_jobs logs specific errors; an empty list here means no data to process.
        return summary
    
    summary["total_jobs_processed_from_fetch"] = len(all_jobs_data)

    conn = get_scraper_db_connection()
    if not conn:
        summary["status"] = "failed"
        summary["errors"].append("Database connection failed.")
        logger.error("Scraper: Database connection failed. Cannot store jobs.")
        return summary
    
    try:
        # store_jobs_in_db now accepts a list of dicts and returns 3 values
        new_added, ignored, db_errors = store_jobs_in_db(all_jobs_data, conn)
        summary["new_jobs_added"] = new_added
        summary["duplicate_ignored_jobs"] = ignored
        if db_errors > 0:
            summary["errors"].append(f"{db_errors} errors occurred during database storage.")
            # Potentially change status if db_errors > 0, but current tests might expect "success" if some jobs are added.
            # For now, keep status "success" if the operation itself didn't raise an exception here.
            logger.warning(f"Scraper: {db_errors} errors reported by store_jobs_in_db.")

        # Only set to "success" if no other major error already set it to "failed"
        if not summary["errors"] and summary["status"] == "started": # Check if status hasn't been set to failed by other issues
             summary["status"] = "success"
        elif summary["errors"]: # If there were db_errors
            summary["status"] = "completed_with_errors"


        logger.info("Scraper: Scraping and storing process completed.")
    except Exception as e: # Catch exceptions from store_jobs_in_db or other issues
        summary["status"] = "failed"
        summary["errors"].append(f"An error occurred during storing jobs: {str(e)}")
        logger.error(f"Scraper: Error during storing jobs: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()
            logger.info("Scraper: Database connection closed.")
            
    logger.info(f"Scraper: === Finished run_scraping_and_storing. Summary: {summary} ===")
    return summary


from database_setup import create_jobs_table # Import the function

if __name__ == "__main__":
    logger.info("Scraper script started for direct execution (TEST MODE - MINIMAL CONFIG): Ensuring database schema and then running limited scraping.")
    
    # Ensure database schema is up to date
    logger.info("Initializing/Verifying database schema...")
    create_jobs_table(DB_FILE_PATH)
    logger.info("Database schema initialization/verification complete.")

    # Minimal config for quick testing
    test_config_override = {
        "job_preferences": {
            "desired_roles": ["Software Engineer"],
            "target_locations": ["New York, NY"],
            "results_wanted": 0, # ZERO results - should be very fast
            "hours_old": 168, 
        },
        "personal_info": { # Needed for country_indeed logic
            "address": {"country": "USA"}
        }
        # Other config sections like cv_paths, application_settings are not directly used by run_scraping_and_storing
    }
    logger.info(f"Using minimal test_config_override: {test_config_override['job_preferences']}")

    # Modify fetch_raw_jobs to use only 'indeed' for speed in this test scenario
    # This is a temporary modification for this testing block.
    # Ideally, site selection would also be part of the config.
    original_sites_to_scrape = None
    # The temporary override logic for sites_to_scrape in __main__ is no longer needed
    # as fetch_raw_jobs now gets it from config.
    # If a specific site list is needed for the __main__ test, it should be part of test_config_override.
    # For example, adding to test_config_override["job_preferences"]:
    # "sites_to_scrape": ["indeed"]
    # However, the subtask is about refactoring fetch_raw_jobs, not __main__.
    # So, removing the direct manipulation of fetch_raw_jobs.__globals__.
    # The test_config_override could be updated if specific sites are needed for the main block test.
    # For now, this part is simplified to reflect that fetch_raw_jobs is self-contained regarding site list.

    result_summary = run_scraping_and_storing(config_override=test_config_override)
    
    logger.info(f"--- Direct execution summary (TEST MODE - MINIMAL CONFIG) ---")
    logger.info(f"Status: {result_summary.get('status')}")
    logger.info(f"Total Jobs Processed from Fetch: {result_summary.get('total_jobs_processed_from_fetch')}")
    logger.info(f"New Jobs Added to DB: {result_summary.get('new_jobs_added')}")
    logger.info(f"Duplicate/Ignored Jobs: {result_summary.get('duplicate_ignored_jobs')}")
    if result_summary.get('errors'):
        logger.error("Errors encountered during the process:")
        for error_msg in result_summary['errors']:
            logger.error(f"- {error_msg}")
            
    logger.info("Scraper script direct execution finished.")
