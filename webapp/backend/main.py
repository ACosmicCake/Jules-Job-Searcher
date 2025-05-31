from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware # Added for CORS
import logging
from logging.handlers import RotatingFileHandler 
import json
from pathlib import Path
from typing import Dict, Any, List, Optional 
import shutil
import os 
import sqlite3 
import pdfplumber # Added pdfplumber import

# --- Project Path Definitions ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE_PATH = PROJECT_ROOT / "config.json"
PARSED_CV_DATA_PATH = PROJECT_ROOT / "parsed_cv_data.json"
CV_UPLOADS_DIR = PROJECT_ROOT / "cv_uploads" 
CV_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = PROJECT_ROOT / "job_listings.db"
LOG_DIR = PROJECT_ROOT / "logs" 
LOG_DIR.mkdir(parents=True, exist_ok=True) 
LOG_FILE_PATH = LOG_DIR / "app_backend.log"

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE_PATH, maxBytes=1024*1024*5, backupCount=3), 
        logging.StreamHandler() 
    ]
)
logger_main = logging.getLogger(__name__) 

# --- Import custom modules (cv_parser, scraper) ---
import sys
sys.path.append(str(PROJECT_ROOT)) 
cv_parser_imported = False
scraper_imported = False
try:
    from cv_parser import process_cv_from_config
    cv_parser_imported = True
    logger_main.info("Successfully imported cv_parser.process_cv_from_config")
except ImportError as e:
    logger_main.error(f"Failed to import from cv_parser: {e}. Ensure cv_parser.py is in PYTHONPATH.")

try:
    from scraper import run_scraping_and_storing, load_scraper_config # Added load_scraper_config
    from database_setup import create_jobs_table # For startup event
    scraper_imported = True
    logger_main.info("Successfully imported from scraper and database_setup.")
except ImportError as e:
    logger_main.error(f"Failed to import from scraper or database_setup: {e}. Ensure .py files are in PYTHONPATH.")
    # Set to None if import fails, to be checked in endpoints
    run_scraping_and_storing = None 
    load_scraper_config = None
    create_jobs_table = None


app = FastAPI(title="AI Job Agent API")

@app.on_event("startup")
async def startup_event():
    logger_main.info("Application startup: Initializing database...")
    if create_jobs_table:
        create_jobs_table(db_path=DB_PATH) # Use DB_PATH from main.py
        logger_main.info("Database initialization complete.")
    else:
        logger_main.error("Could not initialize database: create_jobs_table function not imported.")

# --- CORS Middleware Configuration ---
origins = [
    "http://localhost",         # For direct browser access or simple clients
    "http://localhost:8080",    # Common for Vue CLI, older Angular
    "http://localhost:5173",    # Common for Vite (Vue 3, React default)
    "http://localhost:3000",    # Common for Create React App, Next.js dev
    # Add your production frontend URL here when deploying
    # e.g., "https://your-frontend-domain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    # allow_origins=["*"], # Allows all origins (less secure, use for quick testing if needed)
    allow_credentials=True, # Allows cookies and auth headers
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], # Specify methods or use ["*"]
    allow_headers=["*"], # Allows all headers
)

# --- Pydantic models ---
from pydantic import BaseModel # Ensure BaseModel is imported here for all models
# List, Optional are already imported at the top from typing

class GenerateCVRequest(BaseModel):
    job_ids: List[str]

class ScrapeRequest(BaseModel):
    results_wanted: Optional[int] = None
    hours_old: Optional[int] = None
    sites_to_scrape: Optional[List[str]] = None
    country_indeed: Optional[str] = None
    linkedin_fetch_description: Optional[bool] = None
    # New optional parameters for jobspy
    google_search_term: Optional[str] = None
    distance: Optional[int] = None
    job_type: Optional[str] = None # e.g. fulltime, parttime, contract, internship, temporary
    is_remote: Optional[bool] = None
    easy_apply: Optional[bool] = None # For LinkedIn
    description_format: Optional[str] = None # "html" or "markdown"

# --- Helper functions for config and DB ---
async def _load_app_config() -> Dict[str, Any] | None:
    # ... (content unchanged)
    if not CONFIG_FILE_PATH.is_file():
        logger_main.error(f"Configuration file not found at {CONFIG_FILE_PATH}")
        return None
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger_main.error(f"Error loading or parsing configuration file: {e}", exc_info=True)
        return None

async def _save_app_config(config_data: Dict[str, Any]) -> bool:
    # ... (content unchanged)
    try:
        with open(CONFIG_FILE_PATH, 'w') as f:
            json.dump(config_data, f, indent=2)
        logger_main.info("Configuration file updated successfully via API.")
        return True
    except Exception as e:
        logger_main.error(f"Error writing configuration file via API: {e}", exc_info=True)
        return False

def get_db_conn_for_api() -> sqlite3.Connection | None:
    # ... (content unchanged)
    try:
        if not DB_PATH.exists():
            logger_main.error(f"Database file not found at {DB_PATH}. Please run database_setup.py.")
            return None
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row 
        logger_main.debug(f"API: Successfully connected to database '{DB_PATH}'.")
        return conn
    except sqlite3.Error as e:
        logger_main.error(f"API: Error connecting to database '{DB_PATH}': {e}", exc_info=True)
        return None

# --- API Endpoints ---
@app.get("/")
async def read_root():
    logger_main.info("Root endpoint '/' was called.")
    return {"message": "Welcome to the AI Job Agent API"}

@app.get("/api/config", response_model=Dict[str, Any])
async def get_config_api():
    logger_main.info(f"API: Attempting to read configuration from: {CONFIG_FILE_PATH}")
    config_data = await _load_app_config()
    if config_data is None:
        raise HTTPException(status_code=500, detail="Could not load configuration file.")
    return config_data

@app.post("/api/config")
async def update_config_api(updated_config: Dict[str, Any]):
    logger_main.info(f"API: Attempting to update configuration file: {CONFIG_FILE_PATH}")
    if await _save_app_config(updated_config):
        return {"message": "Configuration updated successfully."}
    else:
        raise HTTPException(status_code=500, detail="Error writing configuration file.")

@app.post("/api/cv/upload")
async def upload_cv(file: UploadFile = File(...)):
    # ... (content unchanged)
    original_filename = file.filename
    file_extension = os.path.splitext(original_filename)[1].lower()
    save_path = CV_UPLOADS_DIR / original_filename
    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger_main.info(f"Successfully uploaded CV: {original_filename} to {save_path}")
    except Exception as e:
        logger_main.error(f"Error saving uploaded CV {original_filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not save uploaded CV: {str(e)}")
    finally:
        file.file.close()

    config_data = await _load_app_config()
    if not config_data:
        raise HTTPException(status_code=500, detail="CV uploaded but failed to update configuration file (config load error).")
    if 'cv_paths' not in config_data:
        config_data['cv_paths'] = {}
    
    path_to_store_in_config = str(save_path.relative_to(PROJECT_ROOT)) if save_path.is_relative_to(PROJECT_ROOT) else str(save_path)

    if file_extension == ".pdf":
        config_data['cv_paths']['pdf'] = path_to_store_in_config
        config_data['cv_paths'].pop('docx', None) 
    elif file_extension in [".docx", ".doc"]:
        config_data['cv_paths']['docx'] = path_to_store_in_config
        config_data['cv_paths'].pop('pdf', None)
    else:
        save_path.unlink(missing_ok=True)
        logger_main.warning(f"Uploaded file {original_filename} is not a PDF or DOCX. File not saved.")
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload PDF or DOCX.")

    if not await _save_app_config(config_data):
        raise HTTPException(status_code=500, detail="CV uploaded but failed to save updated configuration.")
        
    return {"message": "CV uploaded and configuration updated successfully.", "filename": original_filename, "saved_path_in_config": path_to_store_in_config}


def parse_configured_cv_task_wrapper():
    # ... (content unchanged)
    logger_main.info("Background task: Starting CV parsing using process_cv_from_config.")
    if not cv_parser_imported:
        logger_main.error("Background task: cv_parser module not imported. Cannot parse CV.")
        return
    try:
        process_cv_from_config(config_file_path=CONFIG_FILE_PATH, output_json_path=PARSED_CV_DATA_PATH)
        logger_main.info("Background task: CV parsing process completed.")
    except Exception as e:
        logger_main.error(f"Background task: Error during CV parsing process: {e}", exc_info=True)


@app.post("/api/cv/parse")
async def trigger_cv_parsing_api(background_tasks: BackgroundTasks):
    # ... (content unchanged)
    if not cv_parser_imported:
        raise HTTPException(status_code=500, detail="CV Parser module not available.")
    background_tasks.add_task(parse_configured_cv_task_wrapper)
    logger_main.info("API: CV parsing task added to background.")
    return {"message": "CV parsing initiated in the background. Check server logs for status."}

@app.get("/api/cv/data", response_model=Dict[str, Any])
async def get_parsed_cv_data_api():
    # ... (content unchanged)
    logger_main.info(f"API: Attempting to read parsed CV data from: {PARSED_CV_DATA_PATH}")
    if not PARSED_CV_DATA_PATH.is_file():
        logger_main.error(f"Parsed CV data file not found at {PARSED_CV_DATA_PATH}")
        raise HTTPException(status_code=404, detail="Parsed CV data not found. Please run parsing first.")
    try:
        with open(PARSED_CV_DATA_PATH, 'r') as f:
            parsed_data = json.load(f)
        logger_main.info("Parsed CV data read successfully.")
        return parsed_data
    except Exception as e: 
        logger_main.error(f"Error reading or parsing CV data file {PARSED_CV_DATA_PATH}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reading or parsing CV data file: {str(e)}")

# --- Real PDF Text Extraction ---
def extract_text_from_pdf(cv_path: Path) -> str:
    if not cv_path.exists():
        logger_main.error(f"CV PDF file not found at: {cv_path}")
        raise FileNotFoundError(f"CV PDF file not found at: {cv_path}")
    try:
        text = ""
        with pdfplumber.open(cv_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n" # Add newline between pages
        logger_main.info(f"Successfully extracted text from PDF: {cv_path.name}")
        return text.strip()
    except Exception as e:
        logger_main.error(f"Error extracting text from PDF {cv_path}: {e}", exc_info=True)
        raise  # Re-raise the exception to be caught by the endpoint

# --- Mock function for Gemini CV Generation (to be replaced later) ---
def call_gemini_cv_generation_mock(cv_text: str, job_description: str) -> bytes:
    """Placeholder for Gemini API call."""
    logger_main.info(f"MOCK: Calling Gemini for CV generation with CV text (len: {len(cv_text)}) and Job Description (len: {len(job_description)})")
    # Simulate PDF byte content
    return b"%PDF-1.4\n%Dummy PDF content for mock CV generation.\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /MediaBox [0 0 612 792] /Contents 4 0 R /Parent 2 0 R >>\nendobj\n4 0 obj\n<< /Length 50 >>\nstream\nBT\n/F1 24 Tf\n72 720 Td\n(Mock Generated CV) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000055 00000 n \n0000000113 00000 n \n0000000180 00000 n \n0000000278 00000 n \ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n370\n%%EOF"

@app.post("/api/cv/generate-tailored", response_model=List[Dict[str, Any]])
async def generate_tailored_cvs_api(request_data: GenerateCVRequest):
    logger_main.info(f"API: Received request to generate tailored CVs for job IDs: {request_data.job_ids}")
    results = []

    app_config = await _load_app_config()
    if not app_config:
        raise HTTPException(status_code=500, detail="Could not load application configuration.")

    cv_paths = app_config.get('cv_paths', {})
    # Prioritize PDF, then DOCX, then any other key if available.
    cv_path_str = cv_paths.get('pdf') or cv_paths.get('docx')

    if not cv_path_str:
        logger_main.error("API: No CV path found in configuration (cv_paths.pdf or cv_paths.docx).")
        raise HTTPException(status_code=400, detail="No CV found. Please upload a CV first via /api/cv/upload.")

    # Construct absolute path from project root if path is relative
    # Ensure cv_path_str is treated as relative to PROJECT_ROOT if it's not already absolute
    cv_file_path = Path(cv_path_str)
    if not cv_file_path.is_absolute():
        cv_file_path = PROJECT_ROOT / cv_file_path

    logger_main.info(f"API: Attempting to use CV from path: {cv_file_path}")

    try:
        cv_text = extract_text_from_pdf(cv_file_path) # Changed to real function
    except FileNotFoundError: # Specifically for CV file not found on disk
        logger_main.error(f"API: CV file configured at '{cv_file_path}' not found on server.")
        raise HTTPException(status_code=400, detail=f"Configured CV file not found. Please verify CV path or re-upload.")
    except Exception as e: # Catch other errors from PDF extraction (e.g., corrupted file)
        logger_main.error(f"API: Error during CV text extraction from {cv_file_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error processing CV file. It might be corrupted or an unsupported format.")


    for job_id in request_data.job_ids:
        job_description_text = None
        conn = None  # Initialize conn to None
        try:
            conn = get_db_conn_for_api()
            if not conn:
                results.append({"job_id": job_id, "status": "error", "message": "Database connection failed."})
                continue

            cursor = conn.cursor()
            cursor.execute("SELECT description_text FROM jobs WHERE id = ?", (job_id,))
            job_row = cursor.fetchone()

            if job_row and job_row['description_text']:
                job_description_text = job_row['description_text']
            else:
                logger_main.warning(f"API: Job ID {job_id} not found or has no description.")
                results.append({"job_id": job_id, "status": "error", "message": "Job not found or no description available."})
                continue # Skip to next job_id
        except sqlite3.Error as e:
            logger_main.error(f"API: Database error for job ID {job_id}: {e}", exc_info=True)
            results.append({"job_id": job_id, "status": "error", "message": "Database error fetching job details."})
            continue # Skip to next job_id
        finally:
            if conn:
                conn.close()

        if job_description_text:
            try:
                # Mock Gemini API call
                generated_cv_bytes = call_gemini_cv_generation_mock(cv_text, job_description_text)
                # For now, just using a mock filename. Actual file handling will be added later.
                generated_cv_filename = f"generated_cv_for_job_{job_id}.pdf"
                # logger_main.info(f"MOCK: Generated CV bytes length: {len(generated_cv_bytes)} for job {job_id}")

                results.append({
                    "job_id": job_id,
                    "generated_cv_filename": generated_cv_filename,
                    "status": "success",
                    "message": "CV generated (mocked)."
                })
            except Exception as e:
                logger_main.error(f"API: Error during mock CV generation for job ID {job_id}: {e}", exc_info=True)
                results.append({"job_id": job_id, "status": "error", "message": f"Mock CV generation failed: {str(e)}"})

    logger_main.info(f"API: Completed tailored CV generation request. Results: {results}")
    return results

def scrape_jobs_task_wrapper():
    # ... (content unchanged)
    logger_main.info("Background task: Starting job scraping and storing process.")
    if not scraper_imported:
        logger_main.error("Background task: scraper module not imported. Cannot scrape jobs.")
        return {"status": "error", "message": "Scraper module not available."} 
    try:
        summary = run_scraping_and_storing() 
        logger_main.info(f"Background task: Job scraping and storing process completed. Summary: {summary}")
        return summary
    except Exception as e:
        logger_main.error(f"Background task: Error during job scraping process: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.post("/api/jobs/scrape")
async def trigger_job_scraping_api(background_tasks: BackgroundTasks):
    # ... (content unchanged)
    if not scraper_imported:
        raise HTTPException(status_code=500, detail="Job Scraper module not available.")
    background_tasks.add_task(scrape_jobs_task_wrapper)
    logger_main.info("API: Job scraping task added to background.")
    return {"message": "Job scraping process initiated in the background. Check server logs for status and summary."}

# Modified Scrape Jobs Endpoint (POST, with overrides)
# Changed path from /api/scrape-jobs to /scrape-jobs/ to match subtask
@app.post("/scrape-jobs/", response_model=Dict[str, Any]) 
async def scrape_jobs_endpoint_post(request_params: ScrapeRequest = None):
    """
    Triggers the job scraping and storing process synchronously.
    Accepts optional 'results_wanted' and 'hours_old' to override config for this run.
    Returns a summary of the scraping operation.
    """
    logger_main.info(f"API: POST /scrape-jobs/ endpoint called with params: {request_params}")
    if not run_scraping_and_storing or not load_scraper_config:
        logger_main.error("API: Scraper functions (run_scraping_and_storing or load_scraper_config) not available.")
        raise HTTPException(status_code=500, detail="Job Scraper components not available.")

    try:
        # Load base configuration from scraper's own loader
        config_override = load_scraper_config() 
        if not config_override:
            logger_main.error("API: Failed to load base configuration for scraping.")
            raise HTTPException(status_code=500, detail="Could not load base scraping configuration.")

        # Override with request parameters if provided
        if request_params:
            if request_params.results_wanted is not None:
                if 'job_preferences' not in config_override: config_override['job_preferences'] = {}
                config_override['job_preferences']['results_wanted'] = request_params.results_wanted
                logger_main.info(f"API: Overriding 'results_wanted' to {request_params.results_wanted}")
            if request_params.hours_old is not None:
                if 'job_preferences' not in config_override: config_override['job_preferences'] = {}
                config_override['job_preferences']['hours_old'] = request_params.hours_old
                logger_main.info(f"API: Overriding 'hours_old' to {request_params.hours_old}")

            # New parameter: sites_to_scrape
            if request_params.sites_to_scrape is not None:
                if 'job_preferences' not in config_override: config_override['job_preferences'] = {}
                config_override['job_preferences']['sites_to_scrape'] = request_params.sites_to_scrape
                logger_main.info(f"API: Overriding 'sites_to_scrape' to {request_params.sites_to_scrape}")

            # New parameter: country_indeed
            if request_params.country_indeed is not None:
                if 'job_preferences' not in config_override: config_override['job_preferences'] = {}
                # Assuming 'country_indeed' is the key expected by scraper.py within job_preferences
                config_override['job_preferences']['country_indeed'] = request_params.country_indeed
                logger_main.info(f"API: Overriding 'country_indeed' to {request_params.country_indeed}")

            # New parameter: linkedin_fetch_description
            if request_params.linkedin_fetch_description is not None:
                if 'job_preferences' not in config_override: config_override['job_preferences'] = {}
                config_override['job_preferences']['linkedin_fetch_description'] = request_params.linkedin_fetch_description
                logger_main.info(f"API: Overriding 'linkedin_fetch_description' to {request_params.linkedin_fetch_description}")

            # google_search_term
            if request_params.google_search_term is not None:
                if 'job_preferences' not in config_override: config_override['job_preferences'] = {}
                config_override['job_preferences']['google_search_term'] = request_params.google_search_term
                logger_main.info(f"API: Overriding 'google_search_term' to {request_params.google_search_term}")

            # distance
            if request_params.distance is not None:
                if 'job_preferences' not in config_override: config_override['job_preferences'] = {}
                config_override['job_preferences']['distance'] = request_params.distance
                logger_main.info(f"API: Overriding 'distance' to {request_params.distance}")

            # job_type
            if request_params.job_type is not None:
                if 'job_preferences' not in config_override: config_override['job_preferences'] = {}
                config_override['job_preferences']['job_type'] = request_params.job_type
                logger_main.info(f"API: Overriding 'job_type' to {request_params.job_type}")

            # is_remote
            if request_params.is_remote is not None:
                if 'job_preferences' not in config_override: config_override['job_preferences'] = {}
                config_override['job_preferences']['is_remote'] = request_params.is_remote
                logger_main.info(f"API: Overriding 'is_remote' to {request_params.is_remote}")

            # easy_apply
            if request_params.easy_apply is not None:
                if 'job_preferences' not in config_override: config_override['job_preferences'] = {}
                config_override['job_preferences']['easy_apply'] = request_params.easy_apply
                logger_main.info(f"API: Overriding 'easy_apply' to {request_params.easy_apply}")

            # description_format
            if request_params.description_format is not None:
                if 'job_preferences' not in config_override: config_override['job_preferences'] = {}
                config_override['job_preferences']['description_format'] = request_params.description_format
                logger_main.info(f"API: Overriding 'description_format' to {request_params.description_format}")
        
        logger_main.info(f"API: Calling run_scraping_and_storing with config: {config_override}") # Log the final config
        summary = run_scraping_and_storing(config_override=config_override)
        logger_main.info(f"API: run_scraping_and_storing completed. Summary: {summary}")
        
        if summary.get("status") == "failed" or summary.get("errors"):
            logger_main.warning(f"API: Scraping process reported errors: {summary.get('errors')}")
        
        return summary
    except Exception as e:
        logger_main.error(f"API: Unexpected error calling run_scraping_and_storing for /scrape-jobs/: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during job scraping: {str(e)}")

# Modified Get Jobs Endpoint
@app.get("/jobs/", response_model=List[Dict[str, Any]]) # Changed path from /api/jobs to /jobs/
async def list_jobs_api(
    title: Optional[str] = None, 
    location: Optional[str] = None, 
    source: Optional[str] = None, 
    status: Optional[str] = None, 
    skip: int = 0,  # Changed from page to skip
    limit: int = 100 # Default limit 100 as per subtask
):
    conn = get_db_conn_for_api()
    if not conn:
        raise HTTPException(status_code=503, detail="Database service unavailable.")
    try:
        cursor = conn.cursor()
        base_query = "SELECT * FROM jobs"
        # count_query = "SELECT COUNT(*) FROM jobs" # Count query can be added if total is needed in response
        conditions = []
        params = []
        
        # Filtering logic (remains the same)
        if title: conditions.append("title LIKE ?"); params.append(f"%{title}%")
        if location: conditions.append("location LIKE ?"); params.append(f"%{location}%")
        if source: conditions.append("source LIKE ?"); params.append(f"%{source}%")
        if status: conditions.append("status = ?"); params.append(status)
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
            # count_query += " WHERE " + " AND ".join(conditions)
            
        base_query += " ORDER BY id ASC" # Changed order for consistent pagination testing
        # Applied skip and limit as per subtask
        base_query += f" LIMIT ? OFFSET ?"
        params.extend([limit, skip])
        
        cursor.execute(base_query, tuple(params))
        jobs_rows = cursor.fetchall()
        
        # Process rows to convert emails string to list
        processed_jobs = []
        for row in jobs_rows:
            job_dict = dict(row)
            if job_dict.get("emails") and isinstance(job_dict["emails"], str):
                try:
                    job_dict["emails"] = json.loads(job_dict["emails"])
                except json.JSONDecodeError:
                    logger_main.warning(f"Could not parse emails JSON string for job ID {job_dict.get('id')}: {job_dict['emails']}")
                    # Keep as string if parsing fails, or set to None/empty list
            processed_jobs.append(job_dict)
            
        return processed_jobs
    except sqlite3.Error as e:
        logger_main.error(f"API: Database error while listing jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database query error.")
    finally:
        if conn: conn.close()

@app.get("/api/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_detail_api(job_id: str):
    # ... (content unchanged)
    conn = get_db_conn_for_api()
    if not conn: raise HTTPException(status_code=503, detail="Database service unavailable.")
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        job_row = cursor.fetchone()
        if job_row: return dict(job_row)
        else: raise HTTPException(status_code=404, detail="Job not found.")
    except sqlite3.Error as e:
        logger_main.error(f"API: Database error for job ID {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Database query error.")
    finally:
        if conn: conn.close()

@app.get("/api/logs", response_model=Dict[str, List[str]])
async def get_application_logs_api(lines: int = 100):
    # ... (content unchanged)
    if not LOG_FILE_PATH.is_file():
        logger_main.error(f"API: Log file not found at {LOG_FILE_PATH}")
        raise HTTPException(status_code=404, detail="Log file not found.")
    if lines <= 0: lines = 100 
    log_lines_tail = []
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
            log_lines_tail = all_lines[-lines:]
        logger_main.info(f"API: Successfully retrieved last {len(log_lines_tail)} lines from log file.")
        return {"logs": [line.strip() for line in log_lines_tail]} 
    except Exception as e:
        logger_main.error(f"API: Error reading log file {LOG_FILE_PATH}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error reading log file: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger_main.info("Starting Uvicorn server for direct execution (debugging)...")
    uvicorn.run("webapp.backend.main:app", host="0.0.0.0", port=8000, log_level="info", reload=True, workers=1)
