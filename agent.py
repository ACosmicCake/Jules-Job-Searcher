import json

def load_json_file(file_path):
    """
    Loads a JSON file and returns its content as a Python dictionary.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict or None: The loaded JSON data as a dictionary, 
                      or None if an error occurs.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from the file '{file_path}'. Check its format.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading '{file_path}': {e}")
        return None

if __name__ == "__main__":
    print("AI Agent starting...")

    # Load configuration file
    config_data = load_json_file("config.json")

    # Load parsed CV data 
    # Note: 'parsed_cv_data.json' might not exist initially or might be created by cv_parser.py
    # For initial testing of agent.py, we might need to create a dummy 'parsed_cv_data.json'
    # or ensure cv_parser.py has run and created it.
    # The 'test_output.json' created by cv_parser.py's test block is a good candidate for temporary use.
    # For this task, we'll try to load 'parsed_cv_data.json' as specified.
    structured_cv_data = load_json_file("parsed_cv_data.json") 
                                        # or "test_output.json" for immediate testing if cv_parser.py's main was run

    if config_data and structured_cv_data:
        print(f"\nWelcome, {config_data.get('personal_info', {}).get('full_name', 'User')}!")
        print("Configuration data loaded successfully.")
        
        print("Structured CV data loaded successfully.")
        # Example of accessing CV data (add more specific examples once cv_parser populates it robustly)
        if 'skills' in structured_cv_data and structured_cv_data['skills']:
            # This is a placeholder, actual skill structure might differ
            first_skill_category = list(structured_cv_data['skills'].keys())[0] if isinstance(structured_cv_data['skills'], dict) and structured_cv_data['skills'] else "N/A"
            if first_skill_category != "N/A" :
                 print(f"For example, a skill category found in your CV is: {first_skill_category}")
            else:
                 print("CV skills section is present but might be empty or not in expected format yet.")

        elif 'name' in structured_cv_data: # From the test_output.json example
            print(f"Found name in CV data: {structured_cv_data['name']}")
        else:
            print("CV data is loaded, but specific example fields (like skills or name) are not available in the current data.")

        # Further agent logic would go here
        print("\nAgent is ready to proceed with its tasks.")

    elif config_data and not structured_cv_data:
        print(f"\nWelcome, {config_data.get('personal_info', {}).get('full_name', 'User')}!")
        print("Configuration data loaded successfully.")
        print("However, structured CV data ('parsed_cv_data.json') failed to load or was not found.")
        print("Please ensure 'cv_parser.py' has been run successfully to generate this file.")
        print("Agent functionality related to CV content will be limited.")
        # Agent might proceed with limited functionality or wait.

    else: # Handles if config_data is None, or both are None
        print("\nFailed to load necessary configuration data ('config.json').")
        if not structured_cv_data:
            print("Structured CV data ('parsed_cv_data.json') also failed to load or was not found.")
        print("Agent cannot proceed without critical configuration.")

    print("\nAI Agent finished.")
