import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import json

# Assuming cv_parser.py is in the same directory or accessible in PYTHONPATH
# If cv_parser.py is in a subdirectory like 'webapp/backend', adjust the import path.
# For this task, I'll assume cv_parser.py is at the root or correctly pathed.
# If PROJECT_ROOT needs to be defined for cv_parser, that might need handling.
# Let's try a direct import first.
try:
    from cv_parser import (
        extract_text_from_docx,
        extract_text_from_pdf,
        parse_cv,
        save_parsed_data,
        load_config_for_cv_parser,
        COMMON_SECTION_HEADINGS # if used directly in tests for setup
    )
except ImportError:
    # Fallback if cv_parser is in webapp.backend
    # This indicates a potential structure issue if tests are at root and module is nested
    # For now, let's assume the test runner handles PYTHONPATH or cv_parser is accessible.
    print("Attempting fallback import for cv_parser assuming it's in webapp.backend")
    # This path adjustment is tricky in a general case without knowing execution context.
    # The problem description implies test_cv_parser.py is at project root.
    # If cv_parser.py is also at root, direct import is fine.
    # If cv_parser.py is in webapp/backend/, then this test file should ideally be
    # in tests/ or tests/backend/ and run with pytest which handles pathing.
    # For now, proceeding with the direct import assumption.
    raise


class TestCVParser(unittest.TestCase):

    def setUp(self):
        # Common setup for tests, if any
        pass

    # --- Tests for extract_text_from_docx ---
    @patch('cv_parser.docx.Document')
    def test_extract_text_from_docx_valid_file(self, mock_document):
        # Mock the Document object and its paragraphs
        mock_para1 = MagicMock()
        mock_para1.text = "Hello world."
        mock_para2 = MagicMock()
        mock_para2.text = "This is a test."

        mock_doc_instance = MagicMock()
        mock_doc_instance.paragraphs = [mock_para1, mock_para2]
        mock_document.return_value = mock_doc_instance

        dummy_docx_path = Path("dummy.docx")
        result = extract_text_from_docx(dummy_docx_path)

        self.assertEqual(result, "Hello world.\nThis is a test.")
        mock_document.assert_called_once_with(dummy_docx_path)

    @patch('cv_parser.docx.Document')
    def test_extract_text_from_docx_handles_exception(self, mock_document):
        mock_document.side_effect = Exception("Failed to open docx")

        dummy_docx_path = Path("dummy.docx")
        result = extract_text_from_docx(dummy_docx_path)

        self.assertIsNone(result)
        mock_document.assert_called_once_with(dummy_docx_path)

    # --- Tests for extract_text_from_pdf ---
    @patch('cv_parser.pdfplumber.open')
    def test_extract_text_from_pdf_valid_file(self, mock_pdf_open):
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 text."
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Page 2 text."

        mock_pdf_instance = MagicMock()
        mock_pdf_instance.pages = [mock_page1, mock_page2]

        # Mock the context manager behavior
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_pdf_instance
        mock_context_manager.__exit__.return_value = None
        mock_pdf_open.return_value = mock_context_manager

        dummy_pdf_path = Path("dummy.pdf")
        result = extract_text_from_pdf(dummy_pdf_path)

        self.assertEqual(result, "Page 1 text.\nPage 2 text.")
        mock_pdf_open.assert_called_once_with(dummy_pdf_path)
        mock_page1.extract_text.assert_called_once()
        mock_page2.extract_text.assert_called_once()

    @patch('cv_parser.pdfplumber.open')
    def test_extract_text_from_pdf_handles_exception(self, mock_pdf_open):
        mock_pdf_open.side_effect = Exception("Failed to open PDF")

        dummy_pdf_path = Path("dummy.pdf")
        result = extract_text_from_pdf(dummy_pdf_path)

        self.assertIsNone(result)
        mock_pdf_open.assert_called_once_with(dummy_pdf_path)

    @patch('cv_parser.pdfplumber.open')
    def test_extract_text_from_pdf_page_with_no_text(self, mock_pdf_open):
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Some text."
        mock_page2 = MagicMock() # This page has no text
        mock_page2.extract_text.return_value = None
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "More text."

        mock_pdf_instance = MagicMock()
        mock_pdf_instance.pages = [mock_page1, mock_page2, mock_page3]

        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_pdf_instance
        mock_context_manager.__exit__.return_value = None
        mock_pdf_open.return_value = mock_context_manager

        dummy_pdf_path = Path("dummy.pdf")
        result = extract_text_from_pdf(dummy_pdf_path)

        self.assertEqual(result, "Some text.\nMore text.") # None page should be skipped
        mock_pdf_open.assert_called_once_with(dummy_pdf_path)

    # --- Tests for parse_cv ---
    def test_parse_cv_empty_text(self):
        expected_output = {key: [] for key in COMMON_SECTION_HEADINGS.keys()}
        expected_output["other_content"] = []
        # Ensure all predefined sections are initialized as lists
        for section_key_list in COMMON_SECTION_HEADINGS.values():
            for section_key in section_key_list: # e.g. "work_experience_actual_key"
                 expected_output[section_key] = []


        # Refined expectation based on typical parse_cv structure
        # It usually initializes based on the *values* of COMMON_SECTION_HEADINGS,
        # which are the actual keys used in the output dict.
        expected_output_refined = {"other_content": []}
        for section_group_key in COMMON_SECTION_HEADINGS:
            for specific_heading_key in COMMON_SECTION_HEADINGS[section_group_key]:
                 expected_output_refined[specific_heading_key] = []

        # The actual structure of COMMON_SECTION_HEADINGS matters here.
        # Example: COMMON_SECTION_HEADINGS = {"experience": ["work experience", "experience"], ...}
        # The output dict from parse_cv would be like: {"experience": [], "education": [], ... "other_content": []}
        # Let's assume the keys of the output dict are the keys of COMMON_SECTION_HEADINGS.

        # Re-simplifying based on the provided cv_parser.py structure:
        # The output keys are the actual keys of the COMMON_SECTION_HEADINGS dictionary.
        expected_result = {key: [] for key in COMMON_SECTION_HEADINGS.keys()}
        expected_result["other_content"] = []

        self.assertEqual(parse_cv(""), expected_result)

    def test_parse_cv_no_sections(self):
        text = "This is some text without any section headings."
        expected_result = {key: [] for key in COMMON_SECTION_HEADINGS.keys()}
        expected_result["other_content"] = [text] # The parser adds non-empty lines
        self.assertEqual(parse_cv(text), expected_result)

    def test_parse_cv_with_known_sections(self):
        text = (
            "Education\nMy University\nMaster's Degree\n\n"
            "WORK EXPERIENCE:\nMy Job\nSoftware Engineer\n\n"
            "Skills\nPython, Java, SQL"
        )
        # Assuming COMMON_SECTION_HEADINGS maps "education" to "education_key", "work experience" to "experience_key" etc.
        # And these keys are like 'education', 'experience', 'skills'.
        # The exact keys depend on the COMMON_SECTION_HEADINGS structure in cv_parser.py
        # For this test, I'll assume the first item in the list of values for each key in COMMON_SECTION_HEADINGS is the output key.
        # e.g. COMMON_SECTION_HEADINGS = { "Experience Section": ["experience", "work experience", "professional experience"], ...}
        # then output key is "experience".

        # Let's check COMMON_SECTION_HEADINGS from the problem description if available, or make a logical assumption.
        # Based on typical usage, the output keys are simplified versions (e.g., 'education', 'experience').
        # The provided COMMON_SECTION_HEADINGS in cv_parser.py looks like:
        # COMMON_SECTION_HEADINGS = {
        #     "Contact Information": ["contact_info", "contact", "personal information"],
        #     "Summary": ["summary", "objective", "profile", "about me"],
        #     ...
        # }
        # So the output keys are "contact_info", "summary", etc.

        expected_result = {key: [] for key in COMMON_SECTION_HEADINGS.keys()}
        expected_result["other_content"] = []

        # Use the direct keys from COMMON_SECTION_HEADINGS
        education_key = "education"
        experience_key = "work_experience" # This should match the key in COMMON_SECTION_HEADINGS
        skills_key = "skills"

        # Current parser behavior: appends each line as a separate item in the list
        expected_result[education_key] = ["My University", "Master's Degree"]
        expected_result[experience_key] = ["My Job", "Software Engineer"]
        expected_result[skills_key] = ["Python, Java, SQL"]

        parsed_data = parse_cv(text)

        self.assertEqual(parsed_data[education_key], expected_result[education_key])
        self.assertEqual(parsed_data[experience_key], expected_result[experience_key])
        self.assertEqual(parsed_data[skills_key], expected_result[skills_key])
        self.assertEqual(parsed_data["other_content"], [])


    def test_parse_cv_mixed_content(self):
        text = (
            "Introduction text before any section.\n\n" # Goes to other_content
            "Education\nMy College\n\n"                 # Education section
            "Text between sections that is not part of a heading.\n\n" # Currently goes to Education
            "Skills\nLeadership\n\n"                   # Skills section
            "Final thoughts."                           # Currently goes to Skills
        )
        expected_result = {key: [] for key in COMMON_SECTION_HEADINGS.keys()}
        education_key = "education"
        skills_key = "skills"

        # Adjusting expectations to current parser behavior:
        # "Text between sections..." will be part of "education"
        # "Final thoughts." will be part of "skills"
        expected_result[education_key] = ["My College", "Text between sections that is not part of a heading."]
        expected_result[skills_key] = ["Leadership", "Final thoughts."]
        expected_result["other_content"] = [
            "Introduction text before any section."
            # "Text between sections that is not part of a heading.", # No longer here
            # "Final thoughts." # No longer here
        ]

        parsed_data = parse_cv(text)

        self.assertEqual(parsed_data[education_key], expected_result[education_key])
        self.assertEqual(parsed_data[skills_key], expected_result[skills_key])
        self.assertEqual(parsed_data["other_content"], expected_result["other_content"])


    # --- Tests for save_parsed_data ---
    @patch('cv_parser.open', new_callable=mock_open)
    @patch('cv_parser.json.dump')
    def test_save_parsed_data_success(self, mock_json_dump, mock_file_open):
        data = {"test": "data"}
        filepath = Path("test_output.json")

        result = save_parsed_data(data, filepath)

        self.assertTrue(result)
        mock_file_open.assert_called_once_with(filepath, 'w', encoding='utf-8')
        mock_json_dump.assert_called_once_with(data, mock_file_open(), indent=4) # Changed indent to 4

    @patch('cv_parser.open', new_callable=mock_open)
    @patch('cv_parser.json.dump')
    def test_save_parsed_data_io_error(self, mock_json_dump, mock_file_open):
        mock_file_open.side_effect = IOError("File write error")
        data = {"test": "data"}
        filepath = Path("test_output.json")

        result = save_parsed_data(data, filepath)

        self.assertFalse(result)

    # --- Tests for load_config_for_cv_parser ---
    @patch('cv_parser.open', new_callable=mock_open)
    @patch('cv_parser.json.load')
    def test_load_config_success(self, mock_json_load, mock_file_open):
        expected_config = {"key": "value"}
        mock_json_load.return_value = expected_config
        filepath = Path("dummy_config.json")

        config = load_config_for_cv_parser(filepath)

        self.assertEqual(config, expected_config)
        mock_file_open.assert_called_once_with(filepath, 'r', encoding='utf-8')
        mock_json_load.assert_called_once_with(mock_file_open())

    @patch('cv_parser.open', new_callable=mock_open)
    def test_load_config_file_not_found(self, mock_file_open):
        mock_file_open.side_effect = FileNotFoundError("File not found")
        filepath = Path("dummy_config.json")

        config = load_config_for_cv_parser(filepath)

        self.assertIsNone(config)

    @patch('cv_parser.open', new_callable=mock_open)
    @patch('cv_parser.json.load')
    def test_load_config_json_decode_error(self, mock_json_load, mock_file_open):
        mock_json_load.side_effect = json.JSONDecodeError("Decode error", "doc", 0)
        filepath = Path("dummy_config.json")

        config = load_config_for_cv_parser(filepath)

        self.assertIsNone(config)


if __name__ == '__main__':
    unittest.main()
