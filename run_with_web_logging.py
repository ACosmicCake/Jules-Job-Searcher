import logging

# Step 1: Import the webapp's main module to trigger its logging configuration.
# This assumes that simply importing main will execute its logging.basicConfig()
# because it's at the module level (top-level).
try:
    print("Attempting to import webapp.backend.main to set up logging...")
    # To make this import work, we need webapp/backend to be discoverable.
    # The webapp.backend.main script itself adds PROJECT_ROOT to sys.path,
    # but for this import to work, we might need to do it here first,
    # or ensure PYTHONPATH is set, or that this script is run from project root.
    import sys
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).resolve().parent
    sys.path.insert(0, str(PROJECT_ROOT)) # Add project root to allow finding webapp package

    import webapp.backend.main # This should execute main.py's logging setup
    print("Imported webapp.backend.main successfully.")
except ImportError as e:
    print(f"Error importing webapp.backend.main: {e}")
    print("Falling back to basic logging config for this test run.")
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

# Get a logger for this test script
logger = logging.getLogger(__name__)
logger.info("--- run_with_web_logging.py: Logging test script started ---")

# Step 2: Now import and run parts of the agent or other modules
try:
    logger.info("Importing agent...")
    import agent # agent.py should now use the logging config set by main.py
    
    logger.info("Calling agent.run_job_search()...")
    # agent.run_job_search() will internally call scraper functions,
    # and all should use the root logging config.
    # For this test, we only need to ensure some logs are generated.
    # We can simplify by calling a more direct logging function from another module too.
    agent.run_job_search() # This will run the full job search, generating many logs
    
    logger.info("Simulating some other log messages from different modules...")
    # The flags cv_parser_imported and scraper_imported are in webapp.backend.main, not agent.
    # For simplicity of this test script, we'll just emit test logs directly if modules are available.
    # We've already seen that the imports in main.py are working.
    
    # Attempt to get loggers by name and log directly
    try:
        logger_cv_test = logging.getLogger("cv_parser")
        logger_cv_test.info("Direct test INFO message from cv_parser logger.")
        logger_cv_test.warning("Direct test WARNING message from cv_parser logger.")

        logger_scraper_test = logging.getLogger("scraper")
        logger_scraper_test.info("Direct test INFO message from scraper logger.")
        logger_scraper_test.error("Direct test ERROR message from scraper logger.")
    except Exception as e_log_test:
        logger.warning(f"Could not emit direct test logs for cv_parser/scraper: {e_log_test}")

except ImportError as e:
    logger.error(f"Failed to import agent or its dependencies: {e}", exc_info=True)
except Exception as e:
    logger.error(f"An error occurred during the test execution: {e}", exc_info=True)

logger.info("--- run_with_web_logging.py: Logging test script finished ---")
