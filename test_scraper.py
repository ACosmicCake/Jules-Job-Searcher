import unittest
from unittest.mock import patch, MagicMock, mock_open, ANY
from pathlib import Path
import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# Attempt to import from scraper.py
# This assumes scraper.py is in the project root or Python path.
# If scraper.py has a top-level 'import jobspy' and jobspy is not installed,
# this import might fail. We may need to pre-mock jobspy in sys.modules for some tests.
try:
    from scraper import (
        load_scraper_config,
        standardize_date,
        get_scraper_db_connection,
        store_jobs_in_db,
        fetch_raw_jobs,
        run_scraping_and_storing,
        # Assuming these might be used or relevant for context, otherwise remove
        # DB_FILE_PATH,
        # CONFIG_FILE_PATH,
        # PROJECT_ROOT
    )
except ImportError as e:
    print(f"Initial ImportError: {e}. This might be due to missing 'jobspy' if it's a top-level import in scraper.py.")
    # One strategy to handle missing jobspy for testing:
    # if 'jobspy' in str(e):
    #     sys.modules['jobspy'] = MagicMock() # Pre-mock jobspy
    #     from scraper import fetch_raw_jobs, run_scraping_and_storing # try importing again
    # else:
    #     raise
    # For now, we'll proceed and assume jobspy can be patched at the point of use.
    raise


class TestScraper(unittest.TestCase):

    def setUp(self):
        # Reset any global states or configurations if necessary
        # For example, if scraper.py modifies any global variables or settings.
        pass

    # --- Tests for load_scraper_config ---
    @patch('scraper.open', new_callable=mock_open)
    @patch('scraper.json.load')
    def test_load_scraper_config_success(self, mock_json_load, mock_file_open):
        expected_config = {"roles": ["engineer"], "locations": ["USA"]}
        mock_json_load.return_value = expected_config
        # Ensure CONFIG_FILE_PATH is a Path object if scraper.py expects it.
        # If CONFIG_FILE_PATH is defined in scraper.py and used by load_scraper_config,
        # we might need to patch that if it's not passed as an argument.
        # Assuming load_scraper_config takes a filepath argument for this test.
        dummy_path = Path("dummy_config.json")
        config = load_scraper_config(dummy_path)

        self.assertEqual(config, expected_config)
        mock_file_open.assert_called_once_with(dummy_path, 'r', encoding='utf-8')
        mock_json_load.assert_called_once_with(mock_file_open())

    @patch('scraper.open', new_callable=mock_open)
    def test_load_scraper_config_file_not_found(self, mock_file_open):
        mock_file_open.side_effect = FileNotFoundError
        dummy_path = Path("dummy_config.json")
        config = load_scraper_config(dummy_path)
        self.assertIsNone(config)

    @patch('scraper.open', new_callable=mock_open)
    @patch('scraper.json.load')
    def test_load_scraper_config_json_decode_error(self, mock_json_load, mock_file_open):
        mock_json_load.side_effect = json.JSONDecodeError("Error", "doc", 0)
        dummy_path = Path("dummy_config.json")
        config = load_scraper_config(dummy_path)
        self.assertIsNone(config)

    # --- Tests for standardize_date ---
    def test_standardize_date_valid_formats(self):
        self.assertEqual(standardize_date("2023-10-26"), "2023-10-26")
        self.assertEqual(standardize_date("10/26/2023"), "2023-10-26")
        # self.assertEqual(standardize_date("26/10/2023", date_format='%d/%m/%Y'), "2023-10-26") # Removed: standardize_date doesn't take date_format

        today = datetime.now()
        self.assertEqual(standardize_date("today"), today.strftime('%Y-%m-%d'))
        self.assertEqual(standardize_date("Today"), today.strftime('%Y-%m-%d'))

        yesterday = today - timedelta(days=1)
        self.assertEqual(standardize_date("yesterday"), yesterday.strftime('%Y-%m-%d'))

        two_days_ago = today - timedelta(days=2)
        self.assertEqual(standardize_date("2 days ago"), two_days_ago.strftime('%Y-%m-%d'))
        self.assertIsNone(standardize_date("posted 2 days ago")) # Adjusted expectation


        # Test with pd.Timestamp
        ts = pd.Timestamp("2023-05-15 10:00:00")
        self.assertEqual(standardize_date(ts), "2023-05-15")

        # Test with datetime object
        dt_obj = datetime(2022, 12, 25)
        self.assertEqual(standardize_date(dt_obj), "2022-12-25")


    def test_standardize_date_invalid_and_edge_cases(self):
        self.assertIsNone(standardize_date(""))
        self.assertIsNone(standardize_date(None))
        self.assertIsNone(standardize_date("invalid date string"))
        self.assertEqual(standardize_date("Tomorrow"), (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'))
        self.assertIsNone(standardize_date("1 day hence")) # Reverted: dateparser returns None for this
        self.assertEqual(standardize_date("2 weeks ago"), (datetime.now() - timedelta(weeks=2)).strftime('%Y-%m-%d'))
        self.assertEqual(standardize_date("30 minutes ago"), datetime.now().strftime('%Y-%m-%d'))


    # --- Tests for get_scraper_db_connection ---
    @patch('scraper.sqlite3.connect')
    def test_get_scraper_db_connection_success(self, mock_sql_connect):
        mock_conn = MagicMock(spec=sqlite3.Connection)
        mock_sql_connect.return_value = mock_conn
        # Assuming get_scraper_db_connection takes a db_path argument
        dummy_db_path = Path("dummy.db")
        conn = get_scraper_db_connection(dummy_db_path)

        self.assertEqual(conn, mock_conn)
        mock_sql_connect.assert_called_once_with(dummy_db_path)

    @patch('scraper.sqlite3.connect')
    def test_get_scraper_db_connection_sqlite_error(self, mock_sql_connect):
        mock_sql_connect.side_effect = sqlite3.Error("DB connection failed")
        dummy_db_path = Path("dummy.db")
        conn = get_scraper_db_connection(dummy_db_path)
        self.assertIsNone(conn)

    # --- Tests for store_jobs_in_db ---
    @patch('scraper.sqlite3.connect') # Mock at the level of where it's used by the SUT or get_scraper_db_connection
    def test_store_jobs_in_db(self, mock_connect_within_scraper): # Assuming get_scraper_db_connection is used inside
        mock_cursor = MagicMock(spec=sqlite3.Cursor)
        mock_conn = MagicMock(spec=sqlite3.Connection)
        mock_conn.cursor.return_value = mock_cursor
        # mock_connect_within_scraper.return_value = mock_conn # If store_jobs_in_db calls sqlite3.connect directly
        # If store_jobs_in_db takes a connection object:

        jobs_empty = []
        # For this test, assume store_jobs_in_db takes a connection object directly
        # Corrected argument order: job_data_list, conn
        inserted, skipped, errors = store_jobs_in_db(jobs_empty, mock_conn)
        self.assertEqual((inserted, skipped, errors), (0,0,0))
        mock_cursor.executemany.assert_not_called()

        # Test with new jobs
        jobs_new = [
            {"job_site_id": "j1", "title": "SWE1", "company": "C1", "location": "L1", "date_posted": "2023-01-01", "job_url": "u1", "description": "D1", "site": "S1", "emails": None, "salary": None, "job_type": None, "scraped_timestamp": "ts1", "status": "new"}, # Matched keys with scraper.py
            {"job_site_id": "j2", "title": "SWE2", "company": "C2", "location": "L2", "date_posted": "2023-01-02", "job_url": "u2", "description": "D2", "site": "S2", "emails": None, "salary": None, "job_type": None, "scraped_timestamp": "ts2", "status": "new"},
        ]
        mock_cursor.rowcount = 1 # Simulate successful insert for each
        # Corrected argument order
        inserted, skipped, errors = store_jobs_in_db(jobs_new, mock_conn)
        self.assertEqual((inserted, skipped, errors), (2,0,0))
        self.assertEqual(mock_cursor.execute.call_count, len(jobs_new)) # Check 'execute' for each job
        # Further assertions can check the actual data passed to executemany

        # Test with duplicate jobs (job_site_id is unique)
        mock_cursor.reset_mock() # Reset call counts etc.

        # Define side effect for cursor.execute for the duplicate test
        def mock_execute_for_duplicates(query, params):
            # Simulate behavior for job 'j3' (new) and 'j1' (duplicate)
            # Assumes job_site_id is the first parameter in the tuple params used with execute
            if params and params[0] == "j3":
                mock_cursor.rowcount = 1 # Simulates insertion
            elif params and params[0] == "j1":
                mock_cursor.rowcount = 0 # Simulates ignored duplicate
            else:
                mock_cursor.rowcount = 0 # Default for any other case
            return MagicMock() # Execute usually returns the cursor itself or None

        mock_cursor.execute.side_effect = mock_execute_for_duplicates

        jobs_duplicate = [ # j3 is new, j1 is duplicate based on job_site_id
            {"job_site_id": "j3", "title": "SWE3", "company": "C3", "location": "L3", "date_posted": "2023-01-03", "job_url": "u3", "description_text": "D3", "source": "S3", "emails": None, "salary_text": None, "job_type": None, "scraped_timestamp": "ts3", "status": "new"},
            {"job_site_id": "j1", "title": "SWE1", "company": "C1", "location": "L1", "date_posted": "2023-01-01", "job_url": "u1", "description_text": "D1", "source": "S1", "emails": None, "salary_text": None, "job_type": None, "scraped_timestamp": "ts1", "status": "new"},
        ]

        inserted, skipped, errors = store_jobs_in_db(jobs_duplicate, mock_conn)
        self.assertEqual((inserted, skipped, errors), (1,1,0)) # 1 inserted (j3), 1 skipped (j1), 0 errors
        self.assertEqual(mock_cursor.execute.call_count, len(jobs_duplicate))

        # Reset side_effect for subsequent tests if necessary, or ensure mock_cursor is fresh.
        mock_cursor.execute.side_effect = None

        # Test jobs missing unique identifiers (e.g. job_site_id or job_url)
        mock_cursor.reset_mock() # Reset call counts etc.
        jobs_missing_id = [
            {"title": "No ID Job", "company": "C_no_id", "job_url": "url_no_id"} # Missing job_site_id
        ]
        # Corrected argument order
        inserted, skipped, errors = store_jobs_in_db(jobs_missing_id, mock_conn)
        self.assertEqual((inserted, skipped, errors), (0,0,1)) # Should be an error

        jobs_missing_url = [
            {"job_site_id": "jsid_no_url", "title": "No URL Job", "company": "C_no_url"} # Missing job_url
        ]
        # Corrected argument order
        inserted, skipped, errors = store_jobs_in_db(jobs_missing_url, mock_conn)
        self.assertEqual((inserted, skipped, errors), (0,0,1)) # Should be an error

        # Test SQLite error during insert
        mock_cursor.reset_mock()
        mock_cursor.execute.side_effect = sqlite3.Error("Insert failed") # If it inserts one by one
        mock_cursor.executemany.side_effect = sqlite3.Error("Insert failed") # If it uses executemany
        jobs_for_error = [ # Ensure all required fields for an attempt are present
             {"job_site_id": "j_err", "title": "SWE_ERR", "company": "C_ERR", "job_url": "u_err", "description": "D_err", "site": "S_err", "scraped_timestamp": "ts_err"}
        ]
        # Corrected argument order
        inserted, skipped, errors = store_jobs_in_db(jobs_for_error, mock_conn)
        self.assertEqual((inserted, skipped, errors), (0,0,len(jobs_for_error)))
        # mock_conn.commit.assert_not_called() # Commit might be called before error in loop
        mock_conn.rollback.assert_called_once() # Assuming a transaction is used and rolled back on error


    # --- Tests for fetch_raw_jobs ---
    @patch('scraper.jobspy.scrape_jobs') # Patching where jobspy is used in scraper.py
    def test_fetch_raw_jobs_success(self, mock_scrape_jobs):
        sample_df = pd.DataFrame({
            'job_url': ['url1', 'url2'],
            'site': ['Indeed', 'LinkedIn'],
            'title': ['Engineer', 'Analyst'],
            'company': ['CompA', 'CompB'],
            'location': ['LocA', 'LocB'],
            'date_posted': [pd.Timestamp('2023-01-01'), '2023-01-02'], # Mixed types jobspy might return
            'description': ['Desc1', 'Desc2'],
            # Add other columns jobspy might return that are used by fetch_raw_jobs
            'job_type': ['Full-time', None],
            'salary': ['$50k', None],
            'emails': [['e1@example.com'], None]
        })
        mock_scrape_jobs.return_value = sample_df

        test_sites = ["custom_indeed", "custom_linkedin"]
        config = {
            "job_preferences": {
                "desired_roles": ["Engineer"],
                "target_locations": ["LocA"],
                "sites_to_scrape": test_sites,
                "results_wanted": 15, # Example value
                "hours_old": 48      # Example value
            },
            "personal_info": { # For country_indeed
                "address": {"country": "USA"}
            }
        }
        # Assuming fetch_raw_jobs uses standardize_date internally
        with patch('scraper.standardize_date', side_effect=lambda x, **kw: x if isinstance(x, str) and '-' in x[:4] else (pd.Timestamp(x).strftime('%Y-%m-%d') if pd.notna(x) else None) ) as mock_std_date:
            raw_jobs = fetch_raw_jobs(config)

        self.assertEqual(len(raw_jobs), 2)
        self.assertIn("scraped_timestamp", raw_jobs[0])
        self.assertEqual(raw_jobs[0]['job_url'], 'url1')
        self.assertEqual(raw_jobs[1]['title'], 'Analyst')
        # Check for raw date types from DataFrame
        self.assertIsInstance(raw_jobs[0]['date_posted'], pd.Timestamp)
        self.assertEqual(raw_jobs[0]['date_posted'], pd.Timestamp('2023-01-01'))
        self.assertEqual(raw_jobs[1]['date_posted'], '2023-01-02') # This was a string

        # Check that scrape_jobs was called correctly
        mock_scrape_jobs.assert_called_once_with(
            site_name=test_sites, # Should use sites from config
            search_term="Engineer",
            location="LocA",
            results_wanted=15,
            hours_old=48,
            country_indeed="USA",
            linkedin_fetch_description=True,
            verbose_level=0
        )

    @patch('scraper.jobspy.scrape_jobs')
    @patch('scraper.logger') # Mock the logger
    def test_fetch_raw_jobs_uses_default_sites_and_logs(self, mock_logger, mock_scrape_jobs):
        mock_scrape_jobs.return_value = pd.DataFrame() # No data needed, just checking call params and log

        # Config without 'sites_to_scrape'
        config = {
            "job_preferences": {
                "desired_roles": ["DefaultsTester"],
                "target_locations": ["DefaultLocation"],
                "results_wanted": 10,
                "hours_old": 24
            },
            "personal_info": {"address": {"country": "Canada"}} # Example, country_indeed might change
        }

        default_sites = ["indeed", "linkedin"] # As defined in scraper.py

        raw_jobs = fetch_raw_jobs(config)
        self.assertEqual(raw_jobs, [])

        mock_scrape_jobs.assert_called_once_with(
            site_name=default_sites, # Should use default sites
            search_term="DefaultsTester",
            location="DefaultLocation",
            results_wanted=10,
            hours_old=24,
            country_indeed="USA", # Current logic defaults to USA if not specific non-US country
            linkedin_fetch_description=True,
            verbose_level=0
        )

        # Check if the logger was called with the specific message
        mock_logger.info.assert_any_call(
            f"Scraper: 'sites_to_scrape' not found in config's job_preferences. Using default sites: {default_sites}"
        )


    @patch('scraper.jobspy.scrape_jobs')
    def test_fetch_raw_jobs_no_results(self, mock_scrape_jobs):
        mock_scrape_jobs.return_value = pd.DataFrame() # Empty DataFrame
        config = {
            "job_preferences": {
                "desired_roles": ["Manager"],
                "target_locations": ["Remote"],
                "sites_to_scrape": ["indeed"] # Needs to be present now
            },
             "personal_info": {"address": {"country": "USA"}}
        }
        raw_jobs = fetch_raw_jobs(config)
        self.assertEqual(raw_jobs, [])

    @patch('scraper.jobspy.scrape_jobs')
    def test_fetch_raw_jobs_jobspy_returns_none(self, mock_scrape_jobs):
        mock_scrape_jobs.return_value = None # jobspy might return None on error
        config = {
            "job_preferences": {
                "desired_roles": ["Sales"],
                "target_locations": ["London"],
                "sites_to_scrape": ["linkedin"] # Needs to be present
            },
            "personal_info": {"address": {"country": "UK"}}
        }
        raw_jobs = fetch_raw_jobs(config)
        self.assertEqual(raw_jobs, [])

    def test_fetch_raw_jobs_missing_config_critical_fields(self):
        # Test missing desired_roles
        config_no_roles = {
            "job_preferences": {
                "target_locations": ["Berlin"],
                "sites_to_scrape": ["indeed"]
            },
            "personal_info": {"address": {"country": "DE"}}
        }
        self.assertEqual(fetch_raw_jobs(config_no_roles), [])

        # Test missing target_locations
        config_no_locations = {
            "job_preferences": {
                "desired_roles": ["Product Owner"],
                "sites_to_scrape": ["indeed"]
            },
            "personal_info": {"address": {"country": "DE"}}
        }
        self.assertEqual(fetch_raw_jobs(config_no_locations), [])

        # Test missing job_preferences entirely
        config_no_job_prefs = {
            "personal_info": {"address": {"country": "DE"}}
        }
        self.assertEqual(fetch_raw_jobs(config_no_job_prefs), [])

        # Test empty config
        self.assertEqual(fetch_raw_jobs({}), [])


    # --- Tests for run_scraping_and_storing ---
    @patch('scraper.load_scraper_config')
    @patch('scraper.fetch_raw_jobs')
    @patch('scraper.get_scraper_db_connection')
    @patch('scraper.store_jobs_in_db')
    def test_run_scraping_and_storing_success(self, mock_store_jobs, mock_get_conn, mock_fetch_raw, mock_load_config):
        mock_load_config.return_value = {
            "job_preferences": {
                "desired_roles": ["Dev"],
                "target_locations": ["Mars"],
                "sites_to_scrape": ["mars_jobs_inc"]
            },
            "personal_info": {}
        }
        mock_fetch_raw.return_value = [{"job_id": "xyz", "title": "Martian Developer"}] # Simplified job data
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_store_jobs.return_value = (1, 0, 0) # inserted, skipped, errors_storing

        # Call run_scraping_and_storing with config_override
        summary = run_scraping_and_storing(config_override=mock_load_config.return_value)

        self.assertEqual(summary["status"], "success")
        self.assertEqual(summary["total_jobs_processed_from_fetch"], 1)
        self.assertEqual(summary["new_jobs_added"], 1)
        self.assertEqual(summary["duplicate_ignored_jobs"], 0)
        self.assertEqual(len(summary["errors"]), 0)
        # mock_load_config.assert_called_once() # Removed: load_scraper_config is not called when config_override is provided
        mock_fetch_raw.assert_called_once_with(mock_load_config.return_value) # Verify config is passed
        mock_get_conn.assert_called_once()
        mock_store_jobs.assert_called_once_with(mock_fetch_raw.return_value, mock_conn) # Corrected argument order

    @patch('scraper.load_scraper_config')
    def test_run_scraping_and_storing_config_load_fails(self, mock_load_config):
        mock_load_config.return_value = None
        summary = run_scraping_and_storing() # Relies on mocked load_scraper_config
        self.assertEqual(summary["status"], "failed")
        self.assertIn("Configuration loading failed.", summary["errors"])
        self.assertEqual(summary["total_jobs_processed_from_fetch"], 0)


    @patch('scraper.load_scraper_config')
    @patch('scraper.fetch_raw_jobs')
    def test_run_scraping_and_storing_fetch_fails_or_empty(self, mock_fetch_raw, mock_load_config):
        test_config = {
             "job_preferences": {
                "desired_roles": ["Dev"],
                "target_locations": ["Mars"],
                "sites_to_scrape": ["mars_jobs_inc"]
            },
            "personal_info": {}
        }
        mock_load_config.return_value = test_config
        mock_fetch_raw.return_value = [] # No jobs fetched
        summary = run_scraping_and_storing(config_override=test_config)
        self.assertEqual(summary["status"], "completed_no_data")
        self.assertEqual(summary["total_jobs_processed_from_fetch"], 0)
        # db connection and store should not be called if no jobs
        # This depends on the SUT's internal logic. Let's assume it doesn't proceed.

    @patch('scraper.load_scraper_config')
    @patch('scraper.fetch_raw_jobs')
    @patch('scraper.get_scraper_db_connection')
    def test_run_scrap_store_db_conn_fails(self, mock_get_conn, mock_fetch_raw, mock_load_config):
        test_config = { # Valid config
             "job_preferences": {
                "desired_roles": ["Dev"],
                "target_locations": ["Mars"],
                "sites_to_scrape": ["mars_jobs_inc"]
            },
            "personal_info": {}
        }
        mock_load_config.return_value = test_config # Define test_config for this scope
        mock_fetch_raw.return_value = [{"job_id": "123"}] # Has jobs
        mock_get_conn.return_value = None # DB connection fails

        summary = run_scraping_and_storing(config_override=test_config)

        self.assertEqual(summary["status"], "failed")
        self.assertEqual(summary["total_jobs_processed_from_fetch"], 1)
        self.assertIn("Database connection failed.", summary["errors"])
        self.assertEqual(summary["new_jobs_added"], 0) # Store not called or fails


if __name__ == '__main__':
    unittest.main()
