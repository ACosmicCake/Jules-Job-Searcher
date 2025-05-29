import json
import logging # Added for agent-specific logging
import scraper # To use scraper's functions

# Configure logging for the agent if not already configured by another module at a higher level
# This will also affect scraper's logging if scraper doesn't reconfigure.
# Ensure consistent logging format.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')


def load_json_file(file_path):
    """
    Loads a JSON file and returns its content as a Python dictionary.
    (This is agent's own utility, kept separate from scraper's config loading for now)
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        logging.error(f"Agent: File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        logging.error(f"Agent: Could not decode JSON from '{file_path}'. Check format.")
        return None
    except Exception as e:
        logging.error(f"Agent: Unexpected error loading '{file_path}': {e}")
        return None

def run_job_search():
    """
    Initiates the job scraping and storing process.
    """
    logging.info("Agent: Job search process initiated via agent.")
    
    # Load configuration using scraper's function, as scraper needs it in a specific way
    # This assumes scraper.load_config() is the source of truth for scraper's operational config
    scraper_config_data = scraper.load_config() # Uses default "config.json"
    
    if scraper_config_data:
        logging.info("Agent: Scraper configuration loaded successfully.")
        # scraper.fetch_jobs() already handles fetching and storing, and internal logging.
        # It returns the DataFrame of fetched jobs, or None/empty DataFrame on failure.
        fetched_jobs_df = scraper.fetch_jobs(scraper_config_data)
        
        if fetched_jobs_df is not None and not fetched_jobs_df.empty:
            logging.info(f"Agent: Job search process completed. {len(fetched_jobs_df)} jobs were processed by the scraper.")
            # Further actions with fetched_jobs_df could be done here if needed by the agent directly.
        elif fetched_jobs_df is not None and fetched_jobs_df.empty:
            logging.info("Agent: Job search process completed. No new jobs were found or fetched by the scraper.")
        else: # implies None was returned by fetch_jobs
            logging.info("Agent: Job search process completed, but an issue occurred (fetch_jobs returned None). See scraper logs for details.")
    else:
        logging.error("Agent: Failed to load scraper configuration. Job search cannot proceed.")


if __name__ == "__main__":
    logging.info("AI Agent starting...")

    # Load agent's primary configuration (could be the same config.json or a different one)
    # For this task, we assume config.json is the shared source.
    # The agent might use this for its own settings, while scraper uses its loaded version.
    agent_main_config = load_json_file("config.json")

    # Load parsed CV data (remains from original agent.py functionality)
    structured_cv_data = load_json_file("parsed_cv_data.json") 

    if agent_main_config:
        logging.info(f"Agent: Welcome, {agent_main_config.get('personal_info', {}).get('full_name', 'User')}!")
        logging.info("Agent: Main configuration data loaded successfully.")
        
        if structured_cv_data:
            logging.info("Agent: Structured CV data loaded successfully.")
            # Example access as before
            if 'skills' in structured_cv_data and structured_cv_data['skills']:
                first_skill_category = list(structured_cv_data['skills'].keys())[0] if isinstance(structured_cv_data['skills'], dict) and structured_cv_data['skills'] else "N/A"
                if first_skill_category != "N/A" :
                     logging.info(f"Agent: Example skill category from CV: {first_skill_category}")
        else:
            logging.info("Agent: Structured CV data ('parsed_cv_data.json') failed to load or not found.")
            logging.info("Agent: CV-related functionalities might be limited.")

        # --- Triggering the job search process ---
        logging.info("Agent: Proceeding to run job search...")
        run_job_search()
        # --- End of job search trigger ---

        logging.info("Agent: Primary tasks, including job search attempt, are complete.")

    else: 
        logging.error("Agent: Failed to load critical configuration ('config.json'). Agent cannot perform main functions.")

    logging.info("AI Agent finished.")
