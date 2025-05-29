# cv_parser.py

# Placeholder for virtual environment setup and library installation instructions:
#
# To set up a virtual environment and install necessary libraries:
# 1. Create a virtual environment: `python -m venv venv`
# 2. Activate the virtual environment:
#    - On Windows: `venv\Scripts\activate`
#    - On macOS/Linux: `source venv/bin/activate`
# 3. Install required libraries: `pip install python-docx pdfplumber`

import json
import re 
import docx # From python-docx
import pdfplumber
from pathlib import Path # For robust path handling
import logging # For better output messages

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')


# Define common CV section headings (lowercase for case-insensitive matching)
COMMON_SECTION_HEADINGS = {
    "work_experience": ["work experience", "professional experience", "employment history", "experience"],
    "education": ["education", "academic background", "qualifications"],
    "skills": ["skills", "technical skills", "proficiencies"],
    "projects": ["projects", "personal projects", "portfolio"],
    "summary": ["summary", "profile", "objective"],
    "contact": ["contact", "contact information"], # Less structured, often at the top
    "references": ["references"],
    "awards": ["awards", "honors", "recognitions"],
    "publications": ["publications"],
    "languages": ["languages"]
}

def extract_text_from_docx(file_path):
    """
    Extracts text from a DOCX file.
    """
    try:
        doc = docx.Document(file_path)
        full_text = [para.text for para in doc.paragraphs]
        logging.info(f"Successfully extracted text from DOCX: {file_path}")
        return '\n'.join(full_text)
    except Exception as e:
        logging.error(f"Error extracting text from DOCX '{file_path}': {e}")
        return None

def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF file.
    """
    full_text = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                if text:
                    full_text.append(text)
                else:
                    logging.warning(f"No text found on page {i+1} of PDF: {file_path}")
            logging.info(f"Successfully extracted text from PDF: {file_path}")
            return '\n'.join(full_text)
    except Exception as e:
        logging.error(f"Error extracting text from PDF '{file_path}': {e}")
        return None

def parse_cv(text, cv_type="unknown"):
    """
    Parses the extracted text from a CV to identify key sections.
    (This is a simplified version focusing on section identification)
    """
    cv_data = {
        "work_experience": [],
        "education": [],
        "skills": [], # Changed to list for simple text appending for now
        "projects": [],
        "summary": [], # Changed to list
        "contact": [], # Changed to list
        "other_content": [] # For text that doesn't fall into known sections
    }
    # Initialize with all known keys from COMMON_SECTION_HEADINGS for consistency
    for key in COMMON_SECTION_HEADINGS:
        if key not in cv_data: # awards, publications, languages, references
             cv_data[key] = []

    logging.info(f"Starting CV parsing (type: {cv_type})...")
    lines = text.splitlines()
    current_section_key = "other_content" # Default section for lines before first heading

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        line_lower = stripped_line.lower()
        found_new_section = False
        for section_key, headings in COMMON_SECTION_HEADINGS.items():
            for heading_variant in headings:
                # Match if line starts with heading_variant (case-insensitive)
                # Simple match: exact heading or heading followed by colon
                if line_lower == heading_variant or line_lower.startswith(heading_variant + ":"):
                    current_section_key = section_key
                    logging.info(f"Identified section: {current_section_key.replace('_', ' ').title()}")
                    # Do not add the heading itself to the section content here if it's just the heading
                    found_new_section = True 
                    break 
            if found_new_section:
                break
        
        # Add the line to the current section if it's not a heading line itself,
        # or if it is a heading line but we want to include it (e.g. "Skills: Python, Java")
        # For now, if a new section was identified, we assume the line was the heading and skip adding it.
        # This logic needs refinement for actual content aggregation.
        if not found_new_section and current_section_key:
             if isinstance(cv_data.get(current_section_key), list):
                cv_data[current_section_key].append(stripped_line)
             else: # Should not happen if cv_data is initialized correctly with lists
                logging.warning(f"Section key '{current_section_key}' not properly initialized in cv_data or not a list.")
                cv_data["other_content"].append(stripped_line)


    # For now, this function mainly identifies sections and prints them.
    # Actual content extraction into structured formats within sections is a more complex task.
    # The cv_data will contain lists of lines under identified sections.
    logging.info("CV parsing attempt finished.")
    return cv_data

def save_parsed_data(data, output_filename="parsed_cv_data.json"):
    """
    Saves the parsed CV data to a JSON file.
    """
    try:
        with open(output_filename, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Parsed data successfully saved to {output_filename}")
    except IOError as e:
        logging.error(f"Error saving data to {output_filename}: {e}")
    except TypeError as e:
        logging.error(f"Error serializing data to JSON: {e}")

# Copied from scraper.py for standalone config loading in cv_parser
def load_cv_parser_config(config_path="config.json"):
    """Loads the configuration file for CV parser."""
    try:
        config_file = Path(config_path)
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        logging.info(f"CV Parser: Configuration loaded successfully from '{config_path}'.")
        return config_data
    except FileNotFoundError:
        logging.error(f"CV Parser: Error - Configuration file '{config_path}' not found.")
        return None
    except json.JSONDecodeError:
        logging.error(f"CV Parser: Error - Could not decode JSON from '{config_path}'. Check its format.")
        return None
    except Exception as e:
        logging.error(f"CV Parser: An unexpected error occurred while loading '{config_path}': {e}")
        return None

if __name__ == '__main__':
    logging.info("CV Parser script started for direct execution.")
    
    config = load_cv_parser_config()
    if not config:
        logging.error("Exiting: Could not load configuration for CV parser.")
    else:
        cv_paths = config.get("cv_paths", {})
        pdf_path_str = cv_paths.get("pdf")
        docx_path_str = cv_paths.get("docx")

        cv_file_to_parse = None
        cv_type = None
        
        # Prioritize PDF, then DOCX
        if pdf_path_str:
            pdf_file = Path(pdf_path_str)
            if pdf_file.is_file():
                cv_file_to_parse = pdf_file
                cv_type = "pdf"
                logging.info(f"Selected PDF CV for parsing: {cv_file_to_parse}")
            else:
                logging.warning(f"PDF CV path specified ('{pdf_path_str}') but file not found.")
        
        if not cv_file_to_parse and docx_path_str: # If PDF not found or not specified, try DOCX
            docx_file = Path(docx_path_str)
            if docx_file.is_file():
                cv_file_to_parse = docx_file
                cv_type = "docx"
                logging.info(f"Selected DOCX CV for parsing: {cv_file_to_parse}")
            else:
                logging.warning(f"DOCX CV path specified ('{docx_path_str}') but file not found.")
        
        if not cv_file_to_parse:
            logging.error("No valid CV file path found in config.json or files do not exist. Exiting.")
        else:
            full_text = None
            if cv_type == "pdf":
                full_text = extract_text_from_pdf(cv_file_to_parse)
            elif cv_type == "docx":
                full_text = extract_text_from_docx(cv_file_to_parse)
            
            if full_text:
                logging.info(f"Successfully extracted text. Total length: {len(full_text)} characters.")
                # print("\n--- Sample Extracted Text (first 500 chars) ---")
                # print(full_text[:500])
                # print("--- End Sample ---")

                parsed_cv_content = parse_cv(full_text, cv_type)
                
                # For debugging, print the structure of parsed_cv_content
                # logging.info("\n--- Parsed CV Content Structure ---")
                # for section, content in parsed_cv_content.items():
                #     if isinstance(content, list):
                #         logging.info(f"Section: {section} - Items: {len(content)}")
                #     else:
                #         logging.info(f"Section: {section} - Type: {type(content)}")
                # logging.info("--- End Parsed CV Content Structure ---")

                save_parsed_data(parsed_cv_content, "parsed_cv_data.json")
            else:
                logging.error(f"Failed to extract text from {cv_file_to_parse}. Cannot proceed with parsing.")

    # Old sample usage - commented out:
    # sample_cv_text = """
    # John Doe
    # ... (rest of old sample text) ...
    # """
    # print("\n--- Testing parse_cv with sample text ---")
    # parsed_cv_from_text = parse_cv(sample_cv_text, 'text') 
    # print("Returned data from parse_cv (structure):", json.dumps(parsed_cv_from_text, indent=2))
    # print("\n--- Testing save_parsed_data ---")
    # sample_data_to_save = { ... }
    # test_output_filename = "test_output.json"
    # save_parsed_data(sample_data_to_save, test_output_filename)
    # ... (rest of old verification) ...

    logging.info("CV Parser script direct execution finished.")
