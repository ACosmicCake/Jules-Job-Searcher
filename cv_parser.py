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
import re # Added for more flexible section heading matching
import docx
import pdfplumber

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

def extract_text_from_docx(file_path):
    """
    Extracts text from a DOCX file.

    Args:
        file_path (str): The path to the DOCX file.

    Returns:
        str: The full text content of the DOCX file.
    """
    doc = docx.Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF file.

    Args:
        file_path (str): The path to the PDF file.

    Returns:
        str: The combined text content from all pages of the PDF.
    """
    full_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            full_text.append(page.extract_text() or "") # Add empty string if page.extract_text() is None
    return '\n'.join(full_text)

# Updated CV parsing logic
def parse_cv(text, cv_type="unknown"): # Added cv_type, though not used extensively yet
    """
    Parses the extracted text from a CV to identify key sections.

    Args:
        text (str): The text content of the CV.
        cv_type (str): The type of CV file (e.g., 'pdf', 'docx', 'text'), for potential future use.

    Returns:
        dict: A dictionary containing identified sections (content not yet populated).
    """
    cv_data = {
        "work_experience": [],
        "education": [],
        "skills": {}, # Using dict for skills for more structured storage later
        "projects": [],
        "summary": "",
        "contact": {},
        "references": [],
        "awards": [],
        "publications": [],
        "languages": [],
        "other": [] # For text that doesn't fall into known sections
    }
    
    print(f"\nStarting CV parsing (type: {cv_type})...")
    lines = text.splitlines()
    current_section = "other" # Default section

    for line in lines:
        line_lower = line.strip().lower()
        if not line_lower: # Skip empty lines
            continue

        found_section = False
        for section_key, headings in COMMON_SECTION_HEADINGS.items():
            for heading in headings:
                # Using regex for more robust matching (e.g., heading at start of line)
                if re.match(r'^' + re.escape(heading) + r'[:\s]*$', line_lower):
                    current_section = section_key
                    print(f"Identified section: {current_section.replace('_', ' ').title()}")
                    found_section = True
                    break
            if found_section:
                break
        
        # For now, we are just identifying sections. Content population will be next.
        # if not found_section:
        #     # Add line to the current_section if it's not a heading itself
        #     # This logic will be refined later.
        #     if current_section != "other" and line.strip():
        #          pass # cv_data[current_section].append(line.strip()) # Example of appending

    print("CV parsing attempt finished.")
    return cv_data

# Updated save_parsed_data function
def save_parsed_data(data, output_filename="parsed_cv_data.json"):
    """
    Saves the parsed CV data to a JSON file.

    Args:
        data (dict): The dictionary containing the parsed CV data.
        output_filename (str): The name of the file to save the data to.
    """
    try:
        with open(output_filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Parsed data successfully saved to {output_filename}")
    except IOError as e:
        print(f"Error saving data to {output_filename}: {e}")
    except TypeError as e:
        print(f"Error serializing data to JSON: {e}")


if __name__ == '__main__':
    print("CV Parser script initialized for testing.")

    # 1. Define a sample CV text
    sample_cv_text = """
John Doe
john.doe@email.com | (555) 123-4567

Summary
A highly motivated software engineer with 5 years of experience in Python and Java.

Work Experience
Senior Software Engineer, Tech Solutions Inc. (2020 - Present)
- Developed cool stuff.
- Led a team.

Education
Master of Science in Computer Science, My University (2018 - 2020)
Bachelor of Science in Computer Science, My University (2014 - 2018)

Skills
Programming Languages: Python, Java, C++
Databases: MySQL, PostgreSQL, MongoDB
Tools: Git, Docker, Jenkins

Projects
Personal Website (2023)
- Built a personal website using Flask.
    """

    print("\n--- Testing parse_cv with sample text ---")
    # 2. Call parse_cv with the sample text
    # cv_type is 'text' as we are directly providing text content
    parsed_cv_from_text = parse_cv(sample_cv_text, 'text') 
    # At this stage, parse_cv mostly prints identified sections and returns the initialized structure.
    print("Returned data from parse_cv (structure):", json.dumps(parsed_cv_from_text, indent=2))


    print("\n--- Testing save_parsed_data ---")
    # 3. Call save_parsed_data with some sample data
    sample_data_to_save = {
        "name": "Jane Test",
        "email": "jane.test@example.com",
        "experience": [
            {"title": "Developer", "company": "TestCorp", "years": "2"}
        ],
        "skills_found": ["testing", "json"]
    }
    test_output_filename = "test_output.json"
    save_parsed_data(sample_data_to_save, test_output_filename)
    
    # Verification step (optional, but good for testing)
    try:
        with open(test_output_filename, 'r') as f:
            loaded_data = json.load(f)
        print(f"Verification: Successfully loaded data from {test_output_filename}")
        if loaded_data == sample_data_to_save:
            print("Verification: Saved data matches original sample_data_to_save.")
        else:
            print("Verification: Saved data DOES NOT match original sample_data_to_save.")
    except Exception as e:
        print(f"Verification: Error reading back {test_output_filename}: {e}")

    print("\n--- Example of how to use with actual files (commented out) ---")
    # This part remains commented as it requires actual files and paths
    # docx_cv_path = "path/to/your/cv.docx" # Replace with an actual path to test
    # pdf_cv_path = "path/to/your/cv.pdf"   # Replace with an actual path to test
    #
    # if docx_cv_path != "path/to/your/cv.docx" and os.path.exists(docx_cv_path):
    #     print(f"\nExtracting text from DOCX: {docx_cv_path}")
    #     docx_text = extract_text_from_docx(docx_cv_path)
    #     # print("DOCX Text Extracted (first 500 chars):", docx_text[:500])
    #     parsed_data_docx = parse_cv(docx_text, 'docx')
    #     save_parsed_data(parsed_data_docx, "parsed_docx_cv.json")
    # else:
    #     print(f"\nSkipping DOCX test: file not found at {docx_cv_path} or path not changed.")
    #
    # if pdf_cv_path != "path/to/your/cv.pdf" and os.path.exists(pdf_cv_path):
    #     print(f"\nExtracting text from PDF: {pdf_cv_path}")
    #     pdf_text = extract_text_from_pdf(pdf_cv_path)
    #     # print("PDF Text Extracted (first 500 chars):", pdf_text[:500])
    #     parsed_data_pdf = parse_cv(pdf_text, 'pdf')
    #     save_parsed_data(parsed_data_pdf, "parsed_pdf_cv.json")
    # else:
    #     print(f"\nSkipping PDF test: file not found at {pdf_cv_path} or path not changed.")
    print("\nCV Parser script test run finished.")
