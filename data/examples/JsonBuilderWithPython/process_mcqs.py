import json
import os

def flatten_and_reassign_ids(data):
    """
    Traverses the nested JSON structure (Year -> Board -> mcqs) to extract all 
    questions and assigns them a new sequential 'id' starting from 1.
    """
    flat_mcq_list = []
    
    # 1. Traverse the nested structure
    # Data is expected to be a dictionary where keys are years (e.g., "2023")
    for year, year_content in data.items():
        if isinstance(year_content, list):
            # year_content is a list of board containers: [{"ঢাকা বোর্ড ": [...]}, ...]
            for board_container in year_content:
                if isinstance(board_container, dict):
                    # board_container keys are board names (e.g., "ঢাকা বোর্ড ")
                    for board_name, board_content in board_container.items():
                        if isinstance(board_content, list):
                            # board_content is a list of objects containing the 'mcqs' key
                            for mcqs_container in board_content:
                                if isinstance(mcqs_container, dict) and 'mcqs' in mcqs_container:
                                    # This is the final list of questions
                                    for question in mcqs_container['mcqs']:
                                        flat_mcq_list.append(question)

    # 2. Reassign sequential IDs starting from 1
    for index, question in enumerate(flat_mcq_list):
        # We ensure the ID is a sequential integer
        question['id'] = index + 1
        
    return flat_mcq_list

def generate_question_bank():
    """
    Main function to read the input file, process the data, and write the output file.
    NOTE: The input_file path has been updated to match the path in your error.
    """
    # *** CORRECTED PATH HERE ***
    input_file = "mcqs_all_board.json"
    output_file = "question_bank.json"
    
    try:
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            nested_data = json.load(f)

        # Flatten the structure and reassign IDs
        final_data = flatten_and_reassign_ids(nested_data)
        
        # Write the modified data to the new output file
        with open(output_file, 'w', encoding='utf-8') as f:
            # Use indent=2 for human-readable formatting
            json.dump(final_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Success! Total {len(final_data)} questions processed.")
        print(f"The new file '{output_file}' has been created with auto-incremented IDs.")

    except FileNotFoundError:
        print(f"\n❌ Error: The input file '{input_file}' was not found.")
        print("Please ensure the script is running from the directory that contains the 'all_board_mcq' folder.")
    except json.JSONDecodeError:
        print(f"\n❌ Error: Could not decode JSON from '{input_file}'. Please ensure the file is valid JSON.")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    generate_question_bank()