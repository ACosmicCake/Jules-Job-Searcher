import pytest
from fastapi.testclient import TestClient
import json
from pathlib import Path
import shutil
import os
import time
import sqlite3

# Add project root to sys.path to allow importing webapp.backend.main and other modules
import sys
PROJECT_ROOT_FOR_TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT_FOR_TESTS))

# Import the FastAPI app instance from webapp.backend.main
# This import should happen AFTER sys.path is modified.
# It will also trigger the logging setup in main.py for the first time.
from webapp.backend.main import app

# Instantiate the TestClient
client = TestClient(app)

# --- Test File Paths ---
TEST_DIR = PROJECT_ROOT_FOR_TESTS / "test_artifacts" # A dedicated directory for test files
TEST_CONFIG_JSON = TEST_DIR / "test_config.json"
TEST_PARSED_CV_JSON = TEST_DIR / "test_parsed_cv.json"
TEST_DB = TEST_DIR / "test_job_listings.db"
TEST_LOG_FILE = TEST_DIR / "test_app_backend.log" # main.py will try to create it in PROJECT_ROOT/logs
ACTUAL_LOG_DIR_IN_MAIN = PROJECT_ROOT_FOR_TESTS / "logs" # As defined in main.py
ACTUAL_LOG_FILE_IN_MAIN = ACTUAL_LOG_DIR_IN_MAIN / "app_backend.log" # As defined in main.py
TEST_UPLOADS_DIR = TEST_DIR / "test_cv_uploads"
DUMMY_CV_FOR_UPLOAD = PROJECT_ROOT_FOR_TESTS / "dummy_cv_for_upload.pdf" # Created in previous step

# --- Pytest Fixture for Setup & Teardown ---
@pytest.fixture(scope="function") # "function" scope runs this for each test
def setup_test_environment(monkeypatch):
    # Create test artifacts directory if it doesn't exist
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    TEST_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Monkeypatch paths in webapp.backend.main
    monkeypatch.setattr("webapp.backend.main.PROJECT_ROOT", PROJECT_ROOT_FOR_TESTS) # So that PROJECT_ROOT based paths in main are correct for tests
    monkeypatch.setattr("webapp.backend.main.CONFIG_FILE_PATH", TEST_CONFIG_JSON)
    monkeypatch.setattr("webapp.backend.main.PARSED_CV_DATA_PATH", TEST_PARSED_CV_JSON)
    monkeypatch.setattr("webapp.backend.main.DB_PATH", TEST_DB)
    
    # Monkeypatch log file path for main.py AND its global LOG_FILE_PATH if used by handlers
    # The RotatingFileHandler is set up using LOG_FILE_PATH at module level in main.py.
    # This means we need to be careful about when it's initialized.
    # For simplicity, we'll assume the TestClient re-initializes app states or we ensure clean state.
    # The logging in main.py is configured at module import.
    # This patching might be tricky if handlers are already set.
    # A better way would be for main.py's logging to be configurable via function call or env var.
    # For now, we'll also patch the LOG_DIR and LOG_FILE_PATH that main.py uses for its handler
    monkeypatch.setattr("webapp.backend.main.LOG_DIR", TEST_DIR) 
    monkeypatch.setattr("webapp.backend.main.LOG_FILE_PATH", TEST_DIR / "test_app_backend.log")
    # Re-initialize logging with patched path for file handler (this is a bit of a hack)
    # This won't work as basicConfig is already called. Proper solution is more complex.
    # We'll test the log endpoint by checking the ACTUAL_LOG_FILE_IN_MAIN for now,
    # and accept that test-specific log isolation is hard with current main.py logging setup.
    # For other file operations, the patching of CONFIG_FILE_PATH etc. is key.

    monkeypatch.setattr("webapp.backend.main.CV_UPLOADS_DIR", TEST_UPLOADS_DIR)

    # Also patch paths used by cv_parser.py and scraper.py if they define their own PROJECT_ROOT
    # cv_parser.py uses config_file_path.parent to determine project_root for CV paths.
    # scraper.py defines its own PROJECT_ROOT.
    monkeypatch.setattr("scraper.PROJECT_ROOT", PROJECT_ROOT_FOR_TESTS)
    monkeypatch.setattr("scraper.CONFIG_FILE_PATH", TEST_CONFIG_JSON)
    monkeypatch.setattr("scraper.DB_FILE_PATH", TEST_DB)
    # cv_parser.py's process_cv_from_config is called with absolute paths by main.py, so it should be fine.


    # 2. Create dummy files and DB
    initial_config_data = {
        "personal_info": {"full_name": "Test User", "email": "test@example.com", "address": {"country": "USA"}},
        "job_preferences": {
            "desired_roles": ["Test Engineer"],
            "target_locations": ["Test City"],
            "sites_to_scrape": ["indeed_test_site"] # Added for scraper config test
        },
        "cv_paths": {"pdf": "", "docx": ""}, # Initially empty
        "application_settings": {}
    }
    with open(TEST_CONFIG_JSON, 'w') as f:
        json.dump(initial_config_data, f, indent=2)

    with open(TEST_PARSED_CV_JSON, 'w') as f: # Empty initial parsed CV
        json.dump({}, f)

    # Create an empty DB with schema for job_listings
    # We need to import database_setup logic or replicate it here for the test DB
    # For simplicity, we assume database_setup.py can be called on a specific DB path
    # This requires database_setup.py to be adaptable or run it manually on TEST_DB
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    # Schema aligned with database_setup.py
    cursor.execute("""
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
    """)
    conn.commit()
    conn.close()
    
    # Ensure the actual log directory (used by main.py before patching for tests) exists
    ACTUAL_LOG_DIR_IN_MAIN.mkdir(parents=True, exist_ok=True)
    if ACTUAL_LOG_FILE_IN_MAIN.exists():
         ACTUAL_LOG_FILE_IN_MAIN.unlink() # Clean up actual log file before test run
    (TEST_DIR / "test_app_backend.log").touch() # Create the test log file

    yield # This is where the test runs

    # 4. Teardown: Remove all created test files and directories
    if TEST_CONFIG_JSON.exists(): TEST_CONFIG_JSON.unlink()
    if TEST_PARSED_CV_JSON.exists(): TEST_PARSED_CV_JSON.unlink()
    if TEST_DB.exists(): TEST_DB.unlink()
    if (TEST_DIR / "test_app_backend.log").exists(): (TEST_DIR / "test_app_backend.log").unlink()
    if TEST_UPLOADS_DIR.exists(): shutil.rmtree(TEST_UPLOADS_DIR)
    # Don't remove TEST_DIR itself if other files might be there, or do it if it's exclusive.
    # For now, just removing specific files. If TEST_DIR is exclusive, rmtree it.
    # Check if TEST_DIR is empty, then remove
    if TEST_DIR.exists() and not any(TEST_DIR.iterdir()):
        TEST_DIR.rmdir()


# --- Test Cases ---

# Test /api/config Endpoints
def test_get_config(setup_test_environment):
    response = client.get("/api/config")
    assert response.status_code == 200
    with open(TEST_CONFIG_JSON, 'r') as f:
        expected_config = json.load(f)
    assert response.json() == expected_config

def test_update_config(setup_test_environment):
    new_config_data = {
        "personal_info": {"full_name": "Updated User"},
        "job_preferences": {"desired_roles": ["QA Engineer"]},
        "cv_paths": {"pdf": "new_cv.pdf"},
        "application_settings": {"dark_mode": True}
    }
    response = client.post("/api/config", json=new_config_data)
    assert response.status_code == 200
    assert response.json() == {"message": "Configuration updated successfully."}
    
    with open(TEST_CONFIG_JSON, 'r') as f:
        saved_config = json.load(f)
    assert saved_config == new_config_data

# Test /api/cv/* Endpoints
def test_upload_cv(setup_test_environment):
    assert DUMMY_CV_FOR_UPLOAD.exists(), "Dummy CV for upload must exist"
    with open(DUMMY_CV_FOR_UPLOAD, "rb") as cv_file:
        response = client.post(
            "/api/cv/upload",
            files={"file": (DUMMY_CV_FOR_UPLOAD.name, cv_file, "application/pdf")}
        )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "CV uploaded and configuration updated successfully."
    assert response_data["filename"] == DUMMY_CV_FOR_UPLOAD.name
    
    # Check if file exists in the (monkeypatched) uploads directory
    expected_upload_path_in_test_dir = TEST_UPLOADS_DIR / DUMMY_CV_FOR_UPLOAD.name
    assert expected_upload_path_in_test_dir.exists()

    # Check if config was updated
    with open(TEST_CONFIG_JSON, 'r') as f:
        config = json.load(f)
    
    # Construct expected path relative to PROJECT_ROOT_FOR_TESTS for comparison
    expected_path_in_config = str((TEST_UPLOADS_DIR / DUMMY_CV_FOR_UPLOAD.name).relative_to(PROJECT_ROOT_FOR_TESTS))
    assert config["cv_paths"]["pdf"] == expected_path_in_config

@pytest.mark.xfail(reason="Background task testing is complex without more infrastructure/mocking.")
def test_trigger_cv_parsing_and_get_data(setup_test_environment):
    # 1. Upload a CV first (using the upload logic)
    with open(DUMMY_CV_FOR_UPLOAD, "rb") as cv_file_obj:
        upload_response = client.post("/api/cv/upload", files={"file": (DUMMY_CV_FOR_UPLOAD.name, cv_file_obj, "application/pdf")})
    assert upload_response.status_code == 200
    
    # 2. Trigger parsing
    response_parse = client.post("/api/cv/parse")
    assert response_parse.status_code == 200
    assert response_parse.json() == {"message": "CV parsing initiated in the background. Check server logs for status."}

    # 3. Wait for parsing (this is fragile)
    time.sleep(3) # Give it a few seconds to process

    # 4. Check for parsed data
    assert TEST_PARSED_CV_JSON.exists(), "Parsed CV JSON file was not created."
    response_get_data = client.get("/api/cv/data")
    assert response_get_data.status_code == 200
    parsed_data = response_get_data.json()
    assert "summary" in parsed_data # Basic check for some expected structure
    # A more robust check would be against expected content from DUMMY_CV_FOR_UPLOAD

def test_get_parsed_cv_data_not_found(setup_test_environment):
    if TEST_PARSED_CV_JSON.exists():
        TEST_PARSED_CV_JSON.unlink() # Ensure it doesn't exist
    response = client.get("/api/cv/data")
    assert response.status_code == 404

# Test /api/jobs/* Endpoints
@pytest.mark.xfail(reason="Background task for scraping and reliance on external services make this complex.")
def test_trigger_job_scraping(setup_test_environment):
    # This test assumes jobspy might be mocked in future or run against test servers.
    # For now, it will hit live services if not mocked.
    # Also, scraper.py uses its own PROJECT_ROOT to find config and DB.
    # Ensure TEST_CONFIG_JSON has some roles for scraper.
    with open(TEST_CONFIG_JSON, 'r') as f:
        config = json.load(f)
    config["job_preferences"]["desired_roles"] = ["Test Scraping Role"]
    config["job_preferences"]["target_locations"] = ["Test Scraping City"]
    with open(TEST_CONFIG_JSON, 'w') as f:
        json.dump(config, f)

    response = client.post("/api/jobs/scrape")
    assert response.status_code == 200
    assert response.json() == {"message": "Job scraping process initiated in the background. Check server logs for status and summary."}
    
    time.sleep(10) # Scraping can take time; this is very fragile.

    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    count = cursor.fetchone()[0]
    conn.close()
    assert count > 0 # Expect some jobs to be inserted if scraping worked

def test_list_jobs_empty(setup_test_environment):
    response = client.get("/api/jobs")
    assert response.status_code == 200
    assert response.json() == []

def test_list_jobs_with_data_and_filters(setup_test_environment):
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    # Insert some test data - aligned with new 14-column schema
    # id, job_site_id, title, company, location, date_posted, job_url, description_text, source, emails, salary_text, job_type, scraped_timestamp, status
    current_time = datetime.now().isoformat()
    jobs_data = [
        (1, "site_id_1", "Software Engineer", "Tech Corp", "New York, NY", "2023-01-01", "url1_unique", "Desc1", "linkedin", '["test1@example.com"]', "100k-120k", "Full-time", current_time, "new"),
        (2, "site_id_2", "Data Scientist", "Data Inc", "New York, NY", "2023-01-02", "url2_unique", "Desc2", "indeed", None, "120k-150k", "Full-time", current_time, "applied"),
        (3, "site_id_3", "Software Engineer", "Another LLC", "Remote", "2023-01-03", "url3_unique", "Desc3", "linkedin", '[]', None, "Contract", current_time, "new"),
    ]
    cursor.executemany("INSERT INTO jobs (id, job_site_id, title, company, location, date_posted, job_url, description_text, source, emails, salary_text, job_type, scraped_timestamp, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", jobs_data)
    conn.commit()
    conn.close()

    # Test without filters
    response = client.get("/jobs/") # UPDATED PATH
    assert response.status_code == 200
    assert len(response.json()) == 3

    # Test with title filter
    response = client.get("/jobs/?title=Software") # UPDATED PATH
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert all("Software Engineer" in job["title"] for job in response.json())

    # Test with location filter
    response = client.get("/jobs/?location=New%20York") # UPDATED PATH & URL encoded space
    assert response.status_code == 200
    assert len(response.json()) == 2

    # Test with source filter
    response = client.get("/jobs/?source=indeed") # UPDATED PATH
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["source"] == "indeed"
    
    # Test with status filter
    response = client.get("/jobs/?status=applied") # UPDATED PATH
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "applied"

    # Test pagination with skip and limit
    # Reminder: Data inserted: (1, "site_id_1", ...), (2, "site_id_2", ...), (3, "site_id_3", ...)

    # Get first record (limit 1, skip 0)
    response = client.get("/jobs/?limit=1&skip=0") # UPDATED PATH & PARAMS
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["job_site_id"] == "site_id_1"

    # Get second record (limit 1, skip 1)
    response = client.get("/jobs/?limit=1&skip=1") # UPDATED PATH & PARAMS
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 2
    assert data[0]["job_site_id"] == "site_id_2"

    # Get first two records (limit 2, skip 0)
    response = client.get("/jobs/?limit=2&skip=0") # UPDATED PATH & PARAMS
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[1]["id"] == 2

    # Get last two records (limit 2, skip 1)
    response = client.get("/jobs/?limit=2&skip=1") # UPDATED PATH & PARAMS
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 2
    assert data[1]["id"] == 3

    # Get third record (limit 1, skip 2)
    response = client.get("/jobs/?limit=1&skip=2") # UPDATED PATH & PARAMS
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 3
    assert data[0]["job_site_id"] == "site_id_3"

    # Try to get records beyond the existing ones (limit 1, skip 3)
    response = client.get("/jobs/?limit=1&skip=3") # UPDATED PATH & PARAMS
    assert response.status_code == 200
    assert len(response.json()) == 0

    # Try to get records with a large limit but skip some (limit 5, skip 1)
    response = client.get("/jobs/?limit=5&skip=1") # UPDATED PATH & PARAMS
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2 # Should return 2nd and 3rd items
    assert data[0]["id"] == 2
    assert data[1]["id"] == 3


def test_get_job_detail(setup_test_environment):
    job_id_int = 100  # Use an integer ID
    job_site_id_text = "test_job_site_id_detail"
    job_url_text = "test_url_detail_unique"
    current_time = datetime.now().isoformat()

    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    # id, job_site_id, title, company, location, date_posted, job_url, description_text, source, emails, salary_text, job_type, scraped_timestamp, status
    job_data = (job_id_int, job_site_id_text, "Detail Job", "Detail Corp", "Remote", "2023-01-04", job_url_text, "Detail Desc", "other", None, "Confidential", "Full-time", current_time, "new")
    cursor.execute("INSERT INTO jobs (id, job_site_id, title, company, location, date_posted, job_url, description_text, source, emails, salary_text, job_type, scraped_timestamp, status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", job_data)
    conn.commit()
    conn.close()

    response = client.get(f"/api/jobs/{job_id_int}") # Use integer ID for API call
    assert response.status_code == 200
    assert response.json()["id"] == job_id_int # Expect integer ID in response
    assert response.json()["title"] == "Detail Job"
    assert response.json()["job_site_id"] == job_site_id_text # Check other fields as well
    assert response.json()["job_url"] == job_url_text

def test_get_job_detail_not_found(setup_test_environment):
    response = client.get("/api/jobs/99999") # Use an integer ID that likely won't exist
    assert response.status_code == 404


# Test /api/logs Endpoint
def test_get_logs(setup_test_environment):
    # This test will check the ACTUAL_LOG_FILE_IN_MAIN due to complexities in patching live handlers
    # Ensure some logs are written by other actions or write dummy lines here.
    # For this test, we'll rely on logs generated by other test client calls.
    
    # Make a few API calls to generate some logs
    client.get("/")
    client.get("/api/config")

    # Now try to get logs
    response = client.get("/api/logs?lines=5") # Ask for 5 lines
    assert response.status_code == 200
    log_data = response.json()
    assert "logs" in log_data
    assert isinstance(log_data["logs"], list)
    # The exact content is hard to assert without knowing what previous tests logged to the *actual* file
    # but we can check if it returned some lines.
    # This test is more of an integration test for the logging setup and endpoint.
    # If the actual log file (ACTUAL_LOG_FILE_IN_MAIN) was cleaned before this test run,
    # then these logs should be from the client.get calls made within this test.
    # If the test environment is truly isolated by the fixture, then the patched log file
    # (TEST_DIR / "test_app_backend.log") should be checked.
    # The current setup_test_environment attempts to patch main.LOG_FILE_PATH, so we should check that.
    
    test_log_path = TEST_DIR / "test_app_backend.log" # The patched path
    # If logging was successfully redirected to the test log path by monkeypatching main.LOG_FILE_PATH
    # *before* the handler was created (which happens on main.py import).
    # This is tricky. The current fixture touches this file.
    # Let's write directly to the patched log file for this test to be certain.
    
    with open(test_log_path, 'a') as f: # Use the patched log path
        f.write("Test log line 1 for /api/logs\n")
        f.write("Test log line 2 for /api/logs\n")
        f.write("Test log line 3 for /api/logs\n")
        f.write("Test log line 4 for /api/logs\n")
        f.write("Test log line 5 for /api/logs\n")
        f.write("Test log line 6 for /api/logs\n")

    response_after_write = client.get("/api/logs?lines=5")
    assert response_after_write.status_code == 200
    log_data_after_write = response_after_write.json()
    assert len(log_data_after_write["logs"]) <= 5 # Should be at most 5
    assert "Test log line 6 for /api/logs" in log_data_after_write["logs"][-1] # Last line
    assert "Test log line 2 for /api/logs" in log_data_after_write["logs"][0] # First of the last 5 (if 6 total)


# Placeholder for other tests if needed
# e.g., test_get_config_not_found, test_update_config_invalid_data (with Pydantic)

from datetime import datetime # Already imported but good for explicitness for the jobs_data variable
