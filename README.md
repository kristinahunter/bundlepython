# TFE Log Analyzer

**⚠️ INTERNAL USE ONLY ⚠️**

This tool is intended for internal use by the team for analyzing Terraform Enterprise log bundles. Please do not distribute it outside of the organization.

## Overview

The TFE Log Analyzer is a Python script designed to quickly scan through a directory of log files (`.log`, `.json`) and identify common issues. It provides several pre-configured searches for known problems and also allows for custom ad-hoc searches.

The primary goal of this tool is to reduce the time it takes to diagnose issues by automating the initial search for common error messages and patterns.

This project was started as an experiment to explore a different approach to log parsing and to build in specific features tailored to my common workflows. It was developed independently without using Bundle Party as a direct reference, and is intended to complement, rather than replace. At this time, Bundle Party has many features not present in the TFE Log Analyzer. 

### AI-Assisted Development

This tool was developed with the assistance of AI. While this has accelerated development, it's important to be aware that there may be undiscovered bugs or unexpected behaviors. Please use the tool critically and report any issues you encounter.

## Getting Started

1.  **Placement:** Place the `log_analyzer.py` script in the root of the extracted log bundle directory.
2.  **Execution:** Run the script from your terminal using Python 3:
    ```bash
    python3 log_analyzer.py
    ```
3.  **Results:** The script will create a directory named `analysis_results` in the same location. Each analysis you run will generate a `.txt` file in this directory containing the matching log lines, prefixed with the source file path.

## How to Use

When you run the script, you will be presented with a main menu with several options:

* **[A] Run All Pre-canned Analyses:** This is the most comprehensive option. It will run every pre-defined search sequentially. This is useful for getting a broad overview of all potential issues in the logs.
* **[Q] Quit / Exit:** This will exit the application.
* **[1-9] Choose a specific analysis:** If you have a specific problem in mind (e.g., you suspect database connection issues), you can select a single, targeted analysis to run.
* **Custom Search:** If none of the pre-canned options fit your needs, you can type your own search terms directly into the prompt.
    * To search for multiple terms at once, separate them with a comma (e.g., `timeout,denied,unreachable`).
    * The results for any custom search will be saved in `analysis_results/custom_search_results.txt`.

After any analysis is complete, you can press **Enter** to return to the main menu to perform another action.

## Contributing & Feedback

This tool is for us, by us. Collaboration is highly encouraged!

* **Report Bugs & Request Features:** If you encounter a bug, have an idea for a new feature, or think a pre-canned search could be improved, please **[open an issue on GitHub](https://github.com/your-username/your-repo/issues)**.
* **Contribute Code:** If you'd like to contribute directly, please feel free to fork the repository and submit a pull request.

Thank you for helping improve this tool!
