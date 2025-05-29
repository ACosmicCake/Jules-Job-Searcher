# cv_parser.py
import json
import re 
import docx # From python-docx
import pdfplumber
from pathlib import Path
import logging

# Ensure this module uses the root logger configured by main.py (or another entry point)
logger = logging.getLogger(__name__) 

# Define common CV section headings (lowercase for case-insensitive matching)
COMMON_SECTION_HEADINGS = {
    "work_experience": ["work experience", "professional experience", "employment history", "experience"],
    "education": ["education", "academic background", "qualifications"],
    "skills": ["skills", "technical skills", "proficiencies"],
    "projects": ["projects", "personal projects", "portfolio"],
    "summary": ["summary", "profile", "objective"],
    "contact": ["contact", "contact information"],
    "references": ["references"],
    "awards": ["awards", "honors", "recognitions"],
    "publications": ["publications"],
    "languages": ["languages"]
}

def extract_text_from_docx(file_path: Path) -> str | None:
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        logger.info(f"Successfully extracted text from DOCX: {file_path}")
        return '\n'.join(full_text)
    except Exception as e:
        logger.error(f"Error extracting text from DOCX '{file_path}': {e}", exc_info=True)
        return None

def extract_text_from_pdf(file_path: Path) -> str | None:
    """Extracts text from a PDF file."""
    full_text = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    full_text.append(text)
                else:
                    logger.warning(f"No text found on page {i+1} of PDF: {file_path}")
            logger.info(f"Successfully extracted text from PDF: {file_path}")
            return '\n'.join(full_text)
    except Exception as e:
        logger.error(f"Error extracting text from PDF '{file_path}': {e}", exc_info=True)
        return None

def parse_cv(text: str, cv_type: str = "unknown") -> dict:
    """Parses the extracted text from a CV to identify key sections."""
    cv_data = {key: [] for key in COMMON_SECTION_HEADINGS}
    cv_data["other_content"] = [] 

    logger.info(f"Starting CV parsing (type: {cv_type})...")
    lines = text.splitlines()
    current_section_key = "other_content" 

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        line_lower = stripped_line.lower()
        found_new_section = False
        for section_key, headings in COMMON_SECTION_HEADINGS.items():
            for heading_variant in headings:
                if line_lower == heading_variant or line_lower.startswith(heading_variant + ":"):
                    current_section_key = section_key
                    logger.debug(f"Identified section: {current_section_key.replace('_', ' ').title()} from heading: '{stripped_line}'")
                    found_new_section = True 
                    break 
            if found_new_section:
                break
        
        if not found_new_section and current_section_key:
             if isinstance(cv_data.get(current_section_key), list):
                cv_data[current_section_key].append(stripped_line)
             else:
                logger.warning(f"Section key '{current_section_key}' not properly initialized or not a list.")
                cv_data["other_content"].append(stripped_line)
    
    logger.info("CV parsing attempt finished.")
    return cv_data

def save_parsed_data(data: dict, output_filename: Path | str) -> bool:
    """Saves the parsed CV data to a JSON file."""
    try:
        output_path = Path(output_filename) 
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=4)
        logger.info(f"Parsed data successfully saved to {output_path}")
        return True
    except IOError as e:
        logger.error(f"Error saving data to {output_path}: {e}", exc_info=True)
    except TypeError as e:
        logger.error(f"Error serializing data to JSON for {output_path}: {e}", exc_info=True)
    return False

def load_config_for_cv_parser(config_path: Path | str) -> dict | None:
    """Loads the configuration file for CV parser."""
    try:
        config_file = Path(config_path)
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        logger.info(f"CV Parser: Configuration loaded successfully from '{config_file}'.")
        return config_data
    except FileNotFoundError:
        logger.error(f"CV Parser: Error - Configuration file '{config_file}' not found.", exc_info=True)
        return None
    except json.JSONDecodeError:
        logger.error(f"CV Parser: Error - Could not decode JSON from '{config_file}'. Check its format.", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"CV Parser: An unexpected error occurred while loading '{config_file}': {e}", exc_info=True)
        return None

def process_cv_from_config(config_file_path: Path | str, 
                           output_json_path: Path | str) -> dict:
    """
    Loads config, finds CV, extracts text, parses, and saves the parsed data.
    Returns a status dictionary.
    """
    summary = {
        "status": "started",
        "message": "",
        "cv_path_used": None,
        "output_path": str(output_json_path) # Store resolved output path
    }
    logger.info(f"CV Parser: Processing CV based on configuration: {config_file_path}")
    
    # Resolve paths passed as arguments if they are not absolute
    # This assumes that if config_file_path is relative, it's relative to CWD from where main.py is run.
    # main.py should pass absolute paths for these.
    abs_config_path = Path(config_file_path).resolve()
    abs_output_json_path = Path(output_json_path).resolve()
    summary["output_path"] = str(abs_output_json_path)


    config = load_config_for_cv_parser(abs_config_path)
    if not config:
        summary["status"] = "error"
        summary["message"] = "Configuration loading failed."
        logger.error(f"CV Parser: Exiting due to configuration load failure from {abs_config_path}.")
        return summary

    cv_paths = config.get("cv_paths", {})
    pdf_path_str = cv_paths.get("pdf")
    docx_path_str = cv_paths.get("docx")

    cv_file_to_parse = None
    cv_type = None
    
    # Project root is determined from the config file's location to resolve relative CV paths
    project_root_for_cv_paths = abs_config_path.parent

    if pdf_path_str:
        pdf_file = (project_root_for_cv_paths / pdf_path_str).resolve()
        if pdf_file.is_file():
            cv_file_to_parse = pdf_file
            cv_type = "pdf"
            logger.info(f"CV Parser: Selected PDF CV for parsing: {cv_file_to_parse}")
        else:
            logger.warning(f"CV Parser: PDF CV path specified ('{pdf_file}') but file not found.")
    
    if not cv_file_to_parse and docx_path_str:
        docx_file = (project_root_for_cv_paths / docx_path_str).resolve()
        if docx_file.is_file():
            cv_file_to_parse = docx_file
            cv_type = "docx"
            logger.info(f"CV Parser: Selected DOCX CV for parsing: {cv_file_to_parse}")
        else:
            logger.warning(f"CV Parser: DOCX CV path specified ('{docx_file}') but file not found.")
    
    if not cv_file_to_parse:
        summary["status"] = "error"
        summary["message"] = "No valid CV file path found in configuration or files do not exist."
        logger.error(summary["message"])
        return summary

    summary["cv_path_used"] = str(cv_file_to_parse)
    full_text = None
    if cv_type == "pdf":
        full_text = extract_text_from_pdf(cv_file_to_parse)
    elif cv_type == "docx":
        full_text = extract_text_from_docx(cv_file_to_parse)
    
    if full_text:
        logger.info(f"CV Parser: Successfully extracted text. Total length: {len(full_text)} characters.")
        parsed_cv_content = parse_cv(full_text, cv_type)
        
        if save_parsed_data(parsed_cv_content, abs_output_json_path):
            summary["status"] = "success"
            summary["message"] = f"CV parsed successfully from {cv_file_to_parse} and saved to {abs_output_json_path}."
            logger.info(summary["message"])
        else:
            summary["status"] = "error"
            summary["message"] = f"Failed to save parsed CV data to {abs_output_json_path}."
            logger.error(summary["message"])
    else:
        summary["status"] = "error"
        summary["message"] = f"Failed to extract text from {cv_file_to_parse}."
        logger.error(summary["message"])
    
    return summary


if __name__ == '__main__':
    # This block is for direct execution.
    # It assumes config.json is in the CWD (project root)
    # and parsed_cv_data.json will be saved in CWD.
    logger.info("CV Parser script started for direct execution.")
    # Get project root assuming this script is in the project root when run directly
    direct_run_project_root = Path.cwd() 
    config_path = direct_run_project_root / "config.json"
    output_path = direct_run_project_root / "parsed_cv_data.json"
    
    result_summary = process_cv_from_config(config_path, output_path)
    logger.info(f"Direct execution summary: {result_summary}")
    logger.info("CV Parser script direct execution finished.")
