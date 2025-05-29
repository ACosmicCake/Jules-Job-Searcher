import json
import logging # Added for agent-specific logging
import scraper # To use scraper's functions

# Configure logging for the agent if not already configured by another module at a higher level
# This will also affect scraper's logging if scraper doesn't reconfigure.
# Ensure consistent logging format.
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s') # Removed: main.py or test script will configure.
logger = logging.getLogger(__name__)


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
        logger.error(f"Agent: File '{file_path}' not found.") # Changed to logger
        return None
    except json.JSONDecodeError:
        logger.error(f"Agent: Could not decode JSON from '{file_path}'. Check format.") # Changed to logger
        return None
    except Exception as e:
        logger.error(f"Agent: Unexpected error loading '{file_path}': {e}") # Changed to logger
        return None

def run_job_search():
    """
    Initiates the job scraping and storing process.
    """
    logger.info("Agent: Job search process initiated via agent.") # Changed to logger
    
    # Load configuration using scraper's function, as scraper needs it in a specific way
    # This assumes scraper.load_scraper_config() is the source of truth for scraper's operational config
    scraper_config_data = scraper.load_scraper_config() # Corrected function name
    
    if scraper_config_data:
        logger.info("Agent: Scraper configuration loaded successfully.") # Changed to logger
        # scraper.fetch_jobs() was the old name, scraper.run_scraping_and_storing() is the new main function in scraper
        # For this agent logic, we just need to ensure the scraper runs. Its summary is logged by itself.
        # The run_scraping_and_storing function in scraper.py handles its own fetching & storing.
        scraper_summary = scraper.run_scraping_and_storing(scraper_config_data) # Pass config
        
        logger.info(f"Agent: Scraper process finished. Summary: {scraper_summary}") # Changed to logger
    else:
        logger.error("Agent: Failed to load scraper configuration. Job search cannot proceed.") # Changed to logger


if __name__ == "__main__":
    # If agent.py is run directly, it needs to set up basic logging FOR ITSELF
    # if no other entry point (like main.py via uvicorn) has done so.
    # However, for this test, we will run it via a script that imports main.py first.
    # So, this direct basicConfig here would be for standalone agent runs only.
    # To avoid double-configuring, we can check if handlers are already present for root logger.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(module)s - %(message)s')

    logger.info("AI Agent starting...") # Changed to logger

    # Load agent's primary configuration (could be the same config.json or a different one)
    # For this task, we assume config.json is the shared source.
    # The agent might use this for its own settings, while scraper uses its loaded version.
    agent_main_config = load_json_file("config.json")

    # Load parsed CV data (remains from original agent.py functionality)
    structured_cv_data = load_json_file("parsed_cv_data.json") 

    if agent_main_config:
        logger.info(f"Agent: Welcome, {agent_main_config.get('personal_info', {}).get('full_name', 'User')}!") # Changed to logger
        logger.info("Agent: Main configuration data loaded successfully.") # Changed to logger
        
        if structured_cv_data:
            logger.info("Agent: Structured CV data loaded successfully.") # Changed to logger
            # Example access as before
            if 'skills' in structured_cv_data and structured_cv_data['skills']:
                first_skill_category = list(structured_cv_data['skills'].keys())[0] if isinstance(structured_cv_data['skills'], dict) and structured_cv_data['skills'] else "N/A"
                if first_skill_category != "N/A" :
                     logger.info(f"Agent: Example skill category from CV: {first_skill_category}") # Changed to logger
        else:
            logger.info("Agent: Structured CV data ('parsed_cv_data.json') failed to load or not found.") # Changed to logger
            logger.info("Agent: CV-related functionalities might be limited.") # Changed to logger

        # --- Triggering the job search process ---
        logger.info("Agent: Proceeding to run job search...") # Changed to logger
        run_job_search()
        # --- End of job search trigger ---

        logger.info("Agent: Primary tasks, including job search attempt, are complete.") # Changed to logger

    else: 
        logger.error("Agent: Failed to load critical configuration ('config.json'). Agent cannot perform main functions.") # Changed to logger

    logger.info("AI Agent finished.") # Changed to logger
