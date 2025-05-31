# AI Job Agent Web Application

## Overview
The AI Job Agent is a web application designed to help manage and automate various aspects of the job search process. It features a FastAPI (Python) backend for core logic and data management, and a Vue.js (Vite) frontend for user interaction. Key functionalities include managing user configurations, parsing CVs, scraping job listings from multiple platforms, and storing relevant data in an SQLite database.

## Features

### Backend API:
*   **Configuration Management:** View and update user settings, job preferences, and file paths via `config.json` through API endpoints.
*   **CV Management:** Upload CV files (PDF, DOCX), trigger parsing in the background, and retrieve parsed CV data.
*   **Job Scraping:** Scrapes job listings from multiple platforms (Indeed, LinkedIn, etc.) using the `python-jobspy` library. Triggered via API and runs as a background task.
*   **Database Storage:** Stores scraped job listings in an SQLite database (`job_listings.db`), automatically handling duplicates.
*   **Job Listing & Details:** API endpoints to list stored jobs with filtering and pagination, and retrieve details for a specific job.
*   **Logging:** Comprehensive backend logging to a rotating file (`logs/app_backend.log`) with an API endpoint to view recent logs.
*   **CORS Enabled:** Configured for cross-origin requests, allowing the frontend (on a different port) to communicate with the API.

### Frontend (Vue.js):
*   **Configuration Editor:** A web interface to view and directly edit the `config.json` content and save changes back to the server.
*   **(Planned)** CV Management UI: Interface for uploading CVs, triggering parsing, and viewing parsed CV data.
*   **(Planned)** Job Listing UI: Interface to display scraped job listings, apply filters, view job details, and manage application status.
*   **(Planned)** Dashboard: Overview of job search progress, statistics, etc.

## Architecture Overview

The application follows a decoupled frontend-backend architecture:

*   **Backend:**
    *   **Framework:** FastAPI (Python)
    *   **Purpose:** Serves API endpoints for all application logic, data processing, and interactions with the database and external services.
    *   **Key Modules:**
        *   `webapp/backend/main.py`: The main FastAPI application, defining API routes and core logic.
        *   `cv_parser.py`: Handles parsing of CV files (DOCX, PDF) to extract text and identify sections.
        *   `scraper.py`: Manages fetching job listings from online platforms using `python-jobspy` and storing them.
        *   `database_setup.py`: Script to initialize the SQLite database schema.
    *   **Database:** SQLite (`job_listings.db`) is used for storing job application data, scraped job listings, etc.
    *   **Configuration:** User-specific data, preferences, and paths are managed via `config.json` in the project root.

*   **Frontend:**
    *   **Framework:** Vue.js 3 with Vite
    *   **Purpose:** Provides the user interface for interacting with the application.
    *   **Location:** `webapp/frontend/`
    *   **Communication:** Interacts with the backend exclusively through the exposed FastAPI endpoints.
    *   **Development:** Requires Node.js and npm for dependency management and running the development server.

## Project Structure

```
.
├── .gitignore
├── README.md
├── agent.py                # Core agent logic (can be integrated further or run standalone)
├── config.json             # User configuration (personal info, job preferences, CV paths)
├── cv_parser.py            # Script for parsing CV files
├── database_setup.py       # Script to set up the SQLite database schema
├── job_listings.db         # SQLite database for storing job data (gitignored)
├── logs/                   # Directory for backend logs
│   └── app_backend.log     # Backend log file (gitignored)
├── parsed_cv_data.json     # Output of CV parsing (gitignored)
├── requirements.txt        # Root requirements file (guidance for setup)
├── run_with_web_logging.py # Utility script for testing logging
├── scraper.py              # Script for scraping job listings
├── start_backend.sh        # Script to start the backend server
├── start_frontend.sh       # Script to start the frontend server
├── tests.py                # Backend test outlines
├── cv_uploads/             # Directory for uploaded CVs (gitignored by default, consider adding)
└── webapp/
    ├── backend/
    │   ├── main.py             # FastAPI application main file
    │   └── requirements.txt    # Python dependencies for the backend
    └── frontend/
        ├── public/
        ├── src/
        │   ├── App.vue
        │   ├── main.js
        │   ├── components/
        │   │   └── ConfigEditor.vue
        │   └── services/
        │       └── api.js
        ├── index.html
        ├── package.json
        ├── package-lock.json
        └── vite.config.js
```

## Setup Instructions

### Prerequisites
*   **Python:** Version 3.8 or newer.
*   **Node.js:** Version 16.x or newer (includes npm).
*   **Git:** For cloning the repository.

### 1. Clone Repository
```bash
git clone <your-repository-url> # Replace with the actual repository URL
cd ai-job-agent # Navigate into the project root
```

### 2. Backend Setup
These steps should be performed from the **project root directory**.
*   **Create and Activate Python Virtual Environment:**
    ```bash
    python -m venv venv
    ```
    Activate it:
    *   On macOS/Linux: `source venv/bin/activate`
    *   On Windows: `venv\Scripts\activate`
*   **Install Python Dependencies:**
    ```bash
    pip install -r webapp/backend/requirements.txt
    ```
    (Also consider `pip install -r requirements.txt` if there are general project dependencies listed there, though primary ones are in `webapp/backend/requirements.txt`)
*   **Initialize/Verify Database:**
    This creates `job_listings.db` with the necessary tables if it doesn't exist.
    ```bash
    python database_setup.py
    ```
    (Note: The backend server now also attempts to initialize the database on startup.)

### 3. Frontend Setup
*   **Navigate to Frontend Directory:**
    ```bash
    cd webapp/frontend
    ```
*   **Install Node.js Dependencies:**
    ```bash
    npm install
    ```
    After this, you might want to return to the project root directory: `cd ../..`

### 4. Configuration (`config.json`)
*   A `config.json` file is located in the project root. Review its structure.
*   **Initial Setup:** Before running the application for the first time, ensure the `cv_paths` within `config.json` point to valid CV files if you intend to use the CV parsing features. You can use the provided `dummy_cv.pdf` or `dummy_cv.docx` for initial testing by setting paths like:
    ```json
    "cv_paths": {
      "pdf": "dummy_cv.pdf",
      "docx": "dummy_cv.docx" 
    }
    ```
    (Ensure these dummy files are in the project root).
*   **Editing via UI:** Once the backend and frontend servers are running, you can edit most of `config.json` directly through the web interface at the "Configuration Editor" page.

## Running the Application

You need to run both the backend and frontend servers simultaneously in separate terminal windows.
The following subsections describe two ways to run the application: manually using `uvicorn` and `npm`, or using the provided start scripts.

### Method 1: Manual Startup

#### 1. Start the Backend Server
*   Ensure your Python virtual environment (e.g., `venv`) is activated.
*   From the **project root directory**:
    ```bash
    uvicorn webapp.backend.main:app --reload --host 0.0.0.0 --port 8000
    ```
    *   `--reload`: Enables auto-reload for development. Uvicorn will watch for code changes.
    *   `--host 0.0.0.0`: Makes the server accessible from your local network (not just `localhost`).
    *   `--port 8000`: Specifies the port.
*   You should see output similar to: `Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)`.
*   The backend API will be available at `http://localhost:8000`.

#### 2. Start the Frontend Development Server
*   Navigate to the **`webapp/frontend` directory**:
    ```bash
    cd webapp/frontend
    ```
*   Run the development server:
    ```bash
    npm run dev
    ```
*   You should see output similar to: `VITE vX.X.X ready in Yms` and provide a Local URL, typically `http://localhost:5173/`.

### Method 2: Using Start Scripts

This is a convenient way to start the servers.

**Prerequisites for Scripts:**
*   Ensure all dependencies are installed as per the "Setup Instructions".
*   The backend `database_setup.py` script should have been run at least once, or rely on the backend server's startup routine to initialize the database.

**Making Scripts Executable (One-time setup):**
Before running the scripts for the first time, you might need to make them executable:
```bash
chmod +x start_backend.sh
chmod +x start_frontend.sh
```

**Starting the Backend with Script:**
To start the backend server, open a terminal window in the **project root directory** and run:
```bash
./start_backend.sh
```
This will start the FastAPI server. Its console output will remain visible in this terminal. Access the API at `http://localhost:8000`.

**Starting the Frontend with Script:**
To start the frontend development server, open another terminal window in the **project root directory** and run:
```bash
./start_frontend.sh
```
This script navigates into `webapp/frontend` and then runs `npm run dev`. The Vue.js development server will start (usually on a port like `http://localhost:5173`). Its console output will remain visible in this terminal.

### Accessing the Application
*   Once both servers are running (either manually or via scripts), open your web browser and navigate to the frontend URL provided by Vite (e.g., `http://localhost:5173`).

### Stopping the Servers
*   To stop either server (whether started manually or with a script), go to its respective terminal window and press `Ctrl+C`.


## Usage / Current Features

*   **Configuration Editor:**
    *   Navigate to the main page of the application in your browser (frontend URL).
    *   The current content of `config.json` (from the project root on the server) will be displayed in a large textarea as a JSON string.
    *   You can directly edit this JSON string. Be careful to maintain valid JSON structure.
    *   Click "Save Configuration" to send the updated JSON to the backend, which will overwrite `config.json`.
    *   Click "Reload Configuration" to fetch and display the latest version from the server.
    *   The "Save" button will be disabled if the JSON in the textarea is not syntactically valid.
    *   **Manual Scrape Parameters**: Input fields for "Results Wanted" and "Hours Old" allow triggering a specific scrape run with these parameters.

*   **Job Listings Display**:
    *   Scraped jobs are displayed below the configuration editor.
    *   **Individual Expand/Collapse**: Each job item has a "Show Details" / "Hide Details" button to toggle the visibility of its full description, salary, job type, etc.
    *   **Pagination**: "Previous" and "Next" buttons allow navigating through pages of job listings.

*   **Triggering Background Tasks (CV Parsing, Default Job Scraping):**
    *   The primary "Scrape Jobs with Parameters" button in the Config Editor section triggers a synchronous scrape.
    *   Older API endpoints for background CV parsing (`POST /api/cv/parse`) and background default job scraping (`POST /api/jobs/scrape`) still exist but may not have dedicated UI buttons yet. These can be initiated using tools like `curl` or Postman.

## Usage Scenarios / End-to-End Testing Guide

This section provides step-by-step instructions for manually testing key end-to-end functionalities.

### Scenario 1: Initial Setup - Configuration, CV Upload, and Parsing

*   **Pre-conditions:**
    *   Backend and frontend servers are running (see "Running the Application").
    *   `config.json` has default/placeholder values.
    *   `parsed_cv_data.json` is empty or non-existent.
    *   You have a sample CV file (e.g., `dummy_cv.pdf` or your own) ready.

*   **Steps:**
    1.  **Access Application:** Open the web app in your browser (e.g., `http://localhost:5173`).
    2.  **Navigate to Configuration:** The "AI Job Agent Configuration" editor should be visible.
    3.  **Update Configuration (Optional):**
        *   Modify a simple field in the JSON editor, e.g., change `full_name` in `personal_info`.
        *   Click "Save Configuration". Verify the success message.
        *   Click "Reload Configuration" and confirm the change is persistent in the textarea.
    4.  **Upload CV:**
        *   **Note:** A UI for CV upload is not yet implemented.
        *   **For current testing:**
            *   Manually ensure `config.json`'s `cv_paths.pdf` (or `docx`) points to your sample CV file (e.g., `"cv_paths": {"pdf": "dummy_cv.pdf", "docx": ""}`). The file should be in the project root or `cv_uploads/` directory if you've modified paths accordingly. If using `dummy_cv.pdf`, ensure it's in the project root.
            *   Alternatively, use a tool like `curl` or Postman to upload a CV to the `POST /api/cv/upload` endpoint.
                Example using `curl` (run from project root, assuming `dummy_cv.pdf` is there):
                ```bash
                curl -X POST -F "file=@dummy_cv.pdf" http://localhost:8000/api/cv/upload
                ```
                Verify the response indicates success and check `config.json` (via UI or file) to see if `cv_paths` was updated.
    5.  **Trigger CV Parsing:**
        *   **Note:** A UI button for this is not yet implemented.
        *   **For current testing:** Use `curl` or Postman to send a POST request to trigger parsing.
            ```bash
            curl -X POST http://localhost:8000/api/cv/parse
            ```
        *   Verify the API response indicates parsing was initiated (e.g., `{"message": "CV parsing initiated in the background..."}`). Check backend logs for details.
    6.  **View Parsed CV Data:**
        *   **Note:** A UI for this is not yet implemented.
        *   **For current testing:** After a short delay for parsing, use `curl` or Postman to get the parsed data:
            ```bash
            curl http://localhost:8000/api/cv/data
            ```
        *   Alternatively, directly inspect the `parsed_cv_data.json` file in the project root.

*   **Expected Outcome:**
    *   `config.json` is updated with the path to the uploaded CV (if uploaded via API).
    *   `parsed_cv_data.json` is created/updated with data extracted from the specified CV.
    *   The `GET /api/cv/data` endpoint returns the content of `parsed_cv_data.json`.

### Scenario 2: Job Scraping and Basic Listing (API Focused)

*   **Pre-conditions:**
    *   Backend and frontend servers are running.
    *   `config.json` has relevant `desired_roles` and `target_locations` (e.g., "Software Engineer" in "New York, NY").
    *   `job_listings.db` is initialized (the `jobs` table exists).

*   **Steps:**
    1.  **Ensure Configuration:** Use the Configuration Editor UI to verify/update `job_preferences` in `config.json` if needed. Save any changes.
    2.  **Trigger Job Scraping (via UI):**
        *   Use the "Manual Scrape Parameters" section in the UI.
        *   Enter desired "Results Wanted" and "Hours Old".
        *   Click "Scrape Jobs with Parameters".
        *   Observe the status message for success or failure.
    3.  **Check Logs (Optional):**
        *   **Note:** A UI for this is not yet implemented.
        *   **For current testing:** Check backend console output or the `logs/app_backend.log` file for scraping activity. You can also use the API:
            ```bash
            curl "http://localhost:8000/api/logs?lines=50"
            ```
    4.  **View Scraped Jobs (UI):**
        *   The `JobList.vue` component below the config editor should update to show the scraped jobs.
        *   Test pagination and individual job detail expansion.
    5.  **View Scraped Jobs (API):**
        *   Use `curl` or Postman to send GET requests to list jobs.
            *   Get first 5 jobs: `curl "http://localhost:8000/jobs/?limit=5"` (Note: path changed from /api/jobs to /jobs/)
            *   Filter by title: `curl "http://localhost:8000/jobs/?title=Engineer&limit=5"`
            *   Filter by location: `curl "http://localhost:8000/jobs/?location=NY&limit=5"` (partial match)


*   **Expected Outcome:**
    *   `job_listings.db` contains new job entries matching the search criteria.
    *   The UI displays these jobs with working pagination and expand/collapse features.
    *   The `/jobs/` API endpoint returns a list of these jobs, and filtering works.

### Note on Future UI Development
Some scenarios above still mention direct API interaction for CV features as their UI is not yet built. The job scraping trigger has been added to the UI.

## API Endpoints Summary

*   `GET    /api/config`: Retrieves the current `config.json`.
*   `POST   /api/config`: Updates `config.json` with the provided JSON body.
*   `POST   /api/cv/upload`: Uploads a CV file (PDF/DOCX). Updates `config.json` with the new path.
*   `POST   /api/cv/parse`: Triggers background parsing of the CV specified in `config.json`.
*   `GET    /api/cv/data`: Retrieves the `parsed_cv_data.json`.
*   `POST   /scrape-jobs/`: Triggers **synchronous** job scraping with parameters from request body and stores results.
*   `POST   /api/jobs/scrape`: Triggers **background** job scraping (using config values) and storing. (This is an older endpoint, new UI uses the synchronous one).
*   `GET    /jobs/`: Lists stored jobs with filters (title, location, source, status) and pagination (skip, limit). (Path updated)
*   `GET    /api/jobs/{job_id}`: Retrieves details for a specific job by its database ID.
*   `GET    /api/logs`: Retrieves the last N lines from the backend log file (`app_backend.log`).

## Troubleshooting (Basic)

*   **CORS Errors:** If the frontend cannot connect to the backend, ensure the frontend's origin (e.g., `http://localhost:5173`) is listed in `allow_origins` in `webapp/backend/main.py`.
*   **Backend Not Running:** If the UI loads but data fetching fails, ensure the backend FastAPI server is running and accessible at `http://localhost:8000`.
*   **Database Not Initialized:** If you see "no such table" errors in backend logs, the backend startup should handle this. If issues persist, you can try manually running `python database_setup.py` from the project root.
*   **Module Not Found (Backend):** Ensure your Python virtual environment is activated and all dependencies from `webapp/backend/requirements.txt` are installed.
*   **Frontend Issues:** Check the browser's developer console for errors. Ensure `npm install` was successful in `webapp/frontend`.

## Testing

*   **Backend:** API tests using FastAPI's `TestClient` and Pytest are in `tests.py`. Run with `pytest -v tests.py` from the project root (ensure virtual env is active and test dependencies installed).
*   **Frontend:** Unit tests for Vue components are in `webapp/frontend/src/components/__tests__`. Run with `npm test` or `npm run test:unit` from the `webapp/frontend` directory.

## Contributing
Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request.

---

*This README provides a general guide. Functionality and specific commands may evolve as the project develops.*
