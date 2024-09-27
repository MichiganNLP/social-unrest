
# Article Metadata and References Fetcher

This repository contains a script to fetch metadata and references for a list of seed papers using their DOIs. The script uses the Web of Science API to retrieve the necessary information and supports recursive fetching of references up to a specified depth.

### Depth Parameter

The depth parameter controls how deep the script will go when recursively fetching references.

- Depth = 1: Only fetch the references of the seed papers.
- Depth = 2: Fetch the references of the seed papers, and also fetch the references of those references.
- Depth = n: Continue this pattern up to n levels deep.

This allows you to control the breadth and depth of the reference tree you want to build.

## Features

- Fetch metadata and UID for seed papers using DOIs.
- Retrieve references for each paper, handling pagination for large numbers of references.
- Extract DOIs from references and recursively fetch their metadata and references.
- Support for breadth-first search (BFS) fetching of references.

## Requirements

- Python 3.x
- `requests` library
- `bibtexparser` library

## Installation

Install the required libraries using pip:

```sh
pip install requests bibtexparser
```

## Setup

### Obtaining an API Key for Web of Science API Expanded Core

To use this script, you'll need an API key for the Web of Science (WOS) Expanded Core API. Follow these steps to get the key:

1. **Register for a WOS Account**: If you don't have an account, sign up on the [Web of Science platform](https://www.webofscience.com/).

2. **Request API Access**: 
   - After logging in, go to the [Web of Science API Portal](https://developer.clarivate.com/apis/wos).
   - Browse to the **WOS Expanded Core Collection API** documentation page.
   - Apply for an API key by following the instructions provided in the portal. Usually, you'll need to provide details about your intended use of the API.
   
3. **Receive API Key**: Once your request is approved, you'll receive an API key. This key will grant access to the WOS Expanded Core API endpoints.

4. **Insert API Key**: Replace the placeholder `'your-api-key'` in the script with the API key you obtained.

### BibTeX File

Prepare a BibTeX file (seedPapers.bib) containing the seed papers. Ensure each entry includes the DOI of the paper.

## Usage

Clone the Repository: Clone this repository to your local machine.

Navigate to the Directory: Open a terminal and navigate to the directory where the repository is cloned.

Run the Script: Execute the script using Python.

```sh
python get_metadata_references_bfs.py
```

After running the script, the results will be available in a folder called `social_unrest_metadata_bfs`. Inside this folder, you will find individual JSON files for each seed paper (e.g., `seed_paper_1.json`, `seed_paper_2.json`), each containing the unique papers identified up to the specified depth.

## Future Enhancements

- Implement the function to fetch the full text of papers using DOIs.
- Improve error handling and logging for better debugging.
- Add support for additional APIs or data sources.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
