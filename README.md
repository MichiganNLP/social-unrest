# Article Metadata and References Fetcher

This repository contains a script to fetch metadata, full text, and references for a list of seed papers using their DOIs. The script uses the Web of Science API to retrieve the necessary information and supports recursive fetching of references up to a specified depth.

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

API Key: Obtain an API key for the Web of Science API. Replace 'your-api-key' in the script with your actual API key.

BibTeX File: Prepare a BibTeX file (seedPapers.bib) containing the seed papers. Ensure each entry includes the DOI of the paper.

## Usage

Clone the Repository: Clone this repository to your local machine.

Navigate to the Directory: Open a terminal and navigate to the directory where the repository is cloned.

Run the Script: Execute the script using Python.

```sh
python get_references_metadata.py
```
After running the script, the final results will be available in the `all_papers_data.json` file.

## Future Enhancements

- Implement the function to fetch the full text of papers using DOIs.
- Improve error handling and logging for better debugging.
- Add support for additional APIs or data sources.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
