import os
import pathlib
import re
import sys

# --- Configuration ---
# The name for the directory where analysis results will be stored.
OUTPUT_DIR_NAME = "analysis_results"

# Define the pre-canned analyses available to the user.
# Each analysis has a display name, a list of search terms (which can be regex),
# an output filename, and a flag indicating if regex should be used.
ANALYSES = {
    # --- Broad, general searches ---
    "1": {
        "name": "General Errors (fail, error, unable)",
        "terms": [
            "fail",
            "error",
            "unable"
        ],
        "ignore_terms": [
            '"auth_error_code":null',
            '"error": ""',
            'Postgres failed to look up setting',
            'TaskResultsErroredWorker',
            'Agent token invalid',
            '/agent/status status=401',
        ],
        "output_file": "general_errors.txt",
        "is_regex": False
    },
    "2": {
        "name": "HTTP Client/Server Errors (4xx/5xx)",
        "terms": [
            r'"status":\s?[45]\d{2}',              # For JSON logs: "status": 404
            r'HTTP/\d\.\d"\s+[45]\d{2}',           # For NGINX logs: "GET /..." 404
            r'status=[45]\d{2}',                   # For logs like: ... status=401
            r'unexpected status code \([45]\d{2}'  # For logs like: ... unexpected status code (401...
        ],
        "output_file": "http_error_codes.txt",
        "is_regex": True
    },
    # --- Specific, diagnostic searches ---
    "3": {
        "name": "Failing Startup Checks",
        "terms": [
            "check failed",
            "startup checks failed"
        ],
        "output_file": "startup_failures.txt",
        "is_regex": False
    },
    "4": {
        "name": "Connection Errors",
        "terms": [
            "failed to connect to",
            "connection refused",
            "error acquiring connection"
        ],
        "output_file": "connection_errors.txt",
        "is_regex": False
    },
    "5": {
        "name": "Vault Seal/Auth Errors",
        "terms": [
            "Error checking seal status",
            "retrieving vault token",
        ],
        "output_file": "vault_errors.txt",
        "is_regex": False
    },
    "6": {
        "name": "Authentication & Credentials",
        "terms": [
            "could not find default credentials",
            "no valid providers in chain",
            "no token provided",
            "unauthenticated",
            "Agent token invalid"
        ],
        "output_file": "auth_credential_errors.txt",
        "is_regex": False
    },
    "7": {
        "name": "Failing Terraform Runs",
        "terms": [
            "Finished handling run with errors",
            "failed running terraform plan"
        ],
        "output_file": "failing_terraform_runs.txt",
        "is_regex": False
    },
    "8": {
        "name": "Notification Delivery Errors",
        "terms": [
            "Unable to deliver",
            "Notifications::DeliveryError"
        ],
        "output_file": "notification_delivery_errors.txt",
        "is_regex": False
    },
     "9": {
        "name": "Webhook Issues",
        "terms": [
            "webhook",
            "webhooks",
            "WebhooksController"
        ],
        "output_file": "webhook_analysis.txt",
        "is_regex": False
    }
}

def run_analysis(search_terms, output_filename, is_regex=False, ignore_terms=None):
    """
    Generic function to search for a list of terms in log files.

    Args:
        search_terms (list): A list of strings or regex patterns to search for.
        output_filename (str): The name of the file to save results to.
        is_regex (bool): If True, treats search_terms as regex patterns.
        ignore_terms (list, optional): A list of strings to ignore. If a line
                                       contains one of these, it's skipped.
    """
    base_path = pathlib.Path('.')
    output_path = base_path / OUTPUT_DIR_NAME
    output_file_path = output_path / output_filename

    # Initialize ignore_terms to an empty list if it's None
    if ignore_terms is None:
        ignore_terms = []

    print("\nStarting analysis...")
    if is_regex:
        print(f"Searching for regex patterns: {', '.join(search_terms)}")
    else:
        print(f"Searching for keywords: {', '.join(search_terms)}")
    
    if ignore_terms:
        print(f"Ignoring lines containing: {', '.join(ignore_terms)}")

    # --- Step 1: Create the output directory ---
    try:
        output_path.mkdir(exist_ok=True)
    except OSError as e:
        print(f"Error: Could not create output directory {output_path.resolve()}. {e}")
        return

    # --- Step 2: Clear old results file if it exists ---
    if output_file_path.exists():
        output_file_path.unlink()

    found_matches = 0
    print("\nSearching files...")

    # --- Step 3: Pre-process search terms for efficiency ---
    compiled_patterns = []
    if is_regex:
        # Compile regex patterns once to avoid repeated work in the loop.
        for pattern in search_terms:
            try:
                compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{pattern}' skipped. Error: {e}", file=sys.stderr)
    else:
        # For simple search, convert terms to lowercase once.
        search_terms = [term.lower() for term in search_terms]
        ignore_terms = [ignore.lower() for ignore in ignore_terms]

    # --- Step 4: Open output file once and walk through all files ---
    try:
        with open(output_file_path, "a", encoding='utf-8') as out_file:
            for dirpath, _, filenames in os.walk(base_path):
                if OUTPUT_DIR_NAME in dirpath:
                    continue

                for filename in filenames:
                    # Search in both .log and .json files
                    if filename.endswith((".log", ".json")):
                        file_path = pathlib.Path(dirpath) / filename
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                for line in f:
                                    matched_term = None
                                    
                                    # Use pre-compiled patterns or pre-lowercased terms
                                    if is_regex:
                                        for pattern in compiled_patterns:
                                            if pattern.search(line):
                                                matched_term = pattern.pattern
                                                break
                                    else:
                                        line_lower = line.lower()
                                        for term in search_terms:
                                            if term in line_lower:
                                                matched_term = term
                                                break
                                    
                                    if matched_term:
                                        # Check if the line should be ignored
                                        line_to_check = line if is_regex else line_lower
                                        if not any(ignore in line_to_check for ignore in ignore_terms):
                                            found_matches += 1
                                            out_file.write(f"[{file_path}] [Matched: '{matched_term}'] {line}")

                        except Exception as e:
                            print(f"Could not read or process file {file_path}: {e}", file=sys.stderr)
    except IOError as e:
        print(f"Error: Could not write to output file {output_file_path}. {e}", file=sys.stderr)


    # --- Step 5: Final Summary ---
    print("\n--------------------")
    print("Analysis Complete.")
    if found_matches > 0:
        print(f"Found {found_matches} matching log entries.")
        print(f"Results have been saved to: {output_file_path.resolve()}")
    else:
        print("No matching log entries were found.")
    print("--------------------")

def main():
    """
    Main function to display the menu and handle user input.
    Loops until the user chooses to exit.
    """
    # Main application loop
    while True:
        # --- MODIFICATION: Display the new, consolidated menu ---
        print("--- Terraform Enterprise Log Analyzer ---")
        print("\nPlease choose an option:")
        print("[A] Run All Pre-canned Analyses")
        print("[Q] Quit / Exit")
        
        print("\n--- Or, choose a specific analysis ---")
        # Sort the analyses by key for consistent ordering
        for key in sorted(ANALYSES.keys(), key=int):
            print(f"[{key}] {ANALYSES[key]['name']}")

        print("\n--- Or, enter your own custom search term(s) (comma-separated) ---")
        choice = input("Enter your choice: ").strip()

        # --- MODIFICATION: Reworked logic to handle new options ---
        if not choice:
            print("No selection made. Please try again.")
            print("\n" * 2)
            continue

        choice_lower = choice.lower()

        if choice_lower == 'q':
            print("Exiting analyzer. Goodbye!")
            break  # Exit the main while loop

        elif choice_lower == 'a':
            print("\n>>> Running ALL pre-canned analyses...")
            # Loop through all analyses and run them sequentially
            for analysis_config in ANALYSES.values():
                print(f"\n--- Running: {analysis_config['name']} ---")
                run_analysis(
                    search_terms=analysis_config["terms"],
                    output_filename=analysis_config["output_file"],
                    is_regex=analysis_config.get("is_regex", False),
                    ignore_terms=analysis_config.get("ignore_terms")
                )
            print("\n>>> All analyses complete.")

        elif choice in ANALYSES:
            # Run a single pre-canned analysis
            analysis_config = ANALYSES[choice]
            print(f"\n--- Running: {analysis_config['name']} ---")
            run_analysis(
                search_terms=analysis_config["terms"],
                output_filename=analysis_config["output_file"],
                is_regex=analysis_config.get("is_regex", False),
                ignore_terms=analysis_config.get("ignore_terms")
            )
        
        else:
            # Run a custom search if the input is not a menu option
            print("\n--- Running Custom Search ---")
            custom_terms = [term.strip() for term in choice.split(',') if term.strip()]
            if custom_terms: 
                run_analysis(
                    search_terms=custom_terms,
                    output_filename="custom_search_results.txt"
                )
            else:
                print("No valid custom search terms were entered.")
        
        # --- MODIFICATION: Pause and wait for user to continue ---
        input("\nPress Enter to return to the main menu...")
        # Add some space for clarity before showing the menu again
        print("\n" * 2)


if __name__ == "__main__":
    main()
