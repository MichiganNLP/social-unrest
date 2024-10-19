import json
import requests
import bibtexparser
import time
from tqdm.notebook import tqdm
import os
from datetime import datetime

current_time = datetime.now()

def fetch_metadata_uid_using_doi(doi, api_key):
    
    """
    Fetches metadata and UID for a given DOI using the Web of Science API.

    Parameters:
    doi (str): The DOI of the paper to fetch metadata for.
    api_key (str): The API key for authenticating with the Web of Science API.

    Returns:
    tuple: A tuple containing the metadata JSON response and the UID string.
    """

    url = f"https://api.clarivate.com/api/wos?databaseId=WOK&usrQuery=DO=({doi})"
    headers = {
        'X-ApiKey': api_key
    }
    # print("Current time from DOI:", datetime.now())
    response = requests.get(url, headers=headers)
    time.sleep(0.5)
    if response.status_code == 200:
        # print(f'\nReceiving response for DOI {doi}:\n{response.json()}')
        uid = ''
        if response.json()['QueryResult']['RecordsFound'] > 0:
            uid = response.json()['Data']['Records']['records']['REC'][0]['UID']
            # print('UID : ', uid.replace(':', '%3A'))
        return response.json(), uid.replace(':', '%3A').replace('(', '%28').replace(')', '%29')

    else:
        print(f"\nError fetching metadata for DOI {doi}: {response.status_code}")
        print("Response Content:", response.content)
        return None, None
    

def fetch_references_using_uid(uid, api_key):

    """
    Fetches all references for a given UID using the Web of Science API, handling pagination.

    Parameters:
    uid (str): The UID of the paper to fetch references for.
    api_key (str): The API key for authenticating with the Web of Science API.

    Returns:
    Dictionary: A dictionary of references. 
    List of references can be accessed using the 'Data' key in the Dictionary.
    """

    all_references = {'Data':[], 'QueryResult':{}}
    first_index = 1
    count = 100

    while True:
        url = f"https://api.clarivate.com/api/wos/references?databaseId=WOK&uniqueId={uid}&count={count}&firstRecord={first_index}"
        headers = {
            'X-ApiKey': api_key
        }
        # print("Current time from Reference:", datetime.now())
        response = requests.get(url, headers=headers)
        time.sleep(0.5)
        if response.status_code == 200:
            references = response.json()
            all_references['Data'].extend(references['Data'])
            all_references['QueryResult'] = references['QueryResult']
            records_found = references.get('QueryResult', {}).get('RecordsFound', 0)
            if first_index + count > records_found:
                break
            first_index += count
        else:
            print(f"\nError fetching references for UID {uid}: {response.status_code}")
            print("Response Content:", response.content)
            break
    # print(f'\nReceiving references for UID {uid}:\n{all_references}\n')
    return all_references


def extract_dois(references):

    """
    Extracts DOIs from a list of references.

    Parameters:
    references (list): A list of reference dictionaries.

    Returns:
    list: A list of DOIs extracted from the references.
    """

    dois = []
    for ref in references['Data']:
        doi = ref.get('DOI')
        if doi:
            doi = doi.replace('/', '%2F').replace('.', '%2E').replace('-', '%2D').replace('(', '%28').replace(')', '%29')
            dois.append(doi)
    return dois


def extract_relevant_metadata(metadata):
    """
    Extracts only the relevant data from the metadata.
    Relevant data includes:
        - 'wos_id': '',
        - 'doi': '',
        - 'title': '',
        - 'authors': [],
        - 'abstract': '',
        - 'keywords': [],
        - 'document_type': [],
        - 'publisher': '',
        - 'publication_year': '',
        - 'publication_date': ''

    Parameters:
    metadata (dict): All metadata for a specific article obtained from WoS.

    Returns:
    dict: A dictionary of all the relevant metadata extracted from the article.
    """
    
    try:
        record = metadata['Data']['Records']['records']['REC'][0]
        wos_id = record.get('UID', '')

        # Extract DOI from identifiers with a try-except block for safety
        doi = ''
        try:
            identifiers = record.get('dynamic_data', {}).get('cluster_related', {}).get('identifiers', {}).get('identifier', [])
            if isinstance(identifiers, list):
                doi = next((id_info['value'] for id_info in identifiers if isinstance(id_info, dict) and id_info.get('type') == 'doi'), '')
            elif isinstance(identifiers, dict) and identifiers.get('type') == 'doi':
                doi = identifiers.get('value', '')
        except Exception as e:
            print(f"Error extracting DOI: {e}")
        
        # Extract title
        title = next((title_info['content'] for title_info in record.get('static_data', {}).get('summary', {}).get('titles', {}).get('title', []) if title_info['type'] == 'item'), '')

        # Extract authors
        authors = []
        try:
            names_data = record.get('static_data', {}).get('summary', {}).get('names', {}).get('name', [])
            if isinstance(names_data, list):
                authors = [author['full_name'] for author in names_data if author['role'] == 'author']
            elif isinstance(names_data, dict) and names_data.get('role') == 'author':
                authors = [names_data.get('full_name', '')]
        except Exception as e:
            print(f"Error extracting authors: {e}")

        # Extract abstract
        abstract = ''
        try:
            abstract_data = record.get('static_data', {}).get('fullrecord_metadata', {}).get('abstracts', {}).get('abstract', {})
            if isinstance(abstract_data, dict):
                abstract = abstract_data.get('abstract_text', {}).get('p', '')
            elif isinstance(abstract_data, list):
                for abs_item in abstract_data:
                    if isinstance(abs_item, dict):
                        abstract = abs_item.get('abstract_text', {}).get('p', '')
                        if abstract:
                            break
        except Exception as e:
            print(f"Error extracting abstract: {e}")

        # Extract keywords
        keywords = record.get('static_data', {}).get('fullrecord_metadata', {}).get('keywords', {}).get('keyword', [])
        
        # Extract document type
        doc_type = record.get('static_data', {}).get('summary', {}).get('doctypes', {}).get('doctype', [])

        # Extract publisher information
        publisher = ''
        try:
            publisher_info = record.get('static_data', {}).get('summary', {}).get('publishers', {}).get('publisher', {})
            if publisher_info:
                publisher = publisher_info.get('names', {}).get('name', {}).get('full_name', '')
        except Exception as e:
            print(f"Error extracting publisher: {e}")

        # Extract publication year and date
        pub_year = ''
        pub_date = ''
        try:
            pub_info = record.get('static_data', {}).get('summary', {}).get('pub_info', {})
            pub_year = pub_info.get('pubyear', '')
            pub_date = pub_info.get('coverdate', '')
        except Exception as e:
            print(f"Error extracting publication info: {e}")

        # Return extracted metadata
        return {
            'wos_id': wos_id,
            'doi': doi,
            'title': title,
            'authors': authors,
            'abstract': abstract,
            'keywords': keywords,
            'document_type': doc_type,
            'publisher': publisher,
            'publication_year': pub_year,
            'publication_date': pub_date
        }

    except (KeyError, IndexError) as e:
        # Handle specific key errors or index errors (missing or malformed data)
        print(f"Error extracting metadata: {e}")
        return {
            'wos_id': '',
            'doi': '',
            'title': '',
            'authors': [],
            'abstract': '',
            'keywords': [],
            'document_type': [],
            'publisher': '',
            'publication_year': '',
            'publication_date': ''
        }
    except Exception as e:
        # Catch any other unexpected errors
        print(f"Unexpected error: {e}")
        return {
            'wos_id': '',
            'doi': '',
            'title': '',
            'authors': [],
            'abstract': '',
            'keywords': [],
            'document_type': [],
            'publisher': '',
            'publication_year': '',
            'publication_date': ''
        }

    

from collections import deque

def process_papers(papers, api_key, depth, visited_dois):
    """
    Processes a list of papers to fetch their metadata and references up to a specified depth using a breadth-first approach.

    Parameters:
    papers (list): A list of paper dictionaries or DOIs (starting level).
    api_key (str): The API key for authenticating with the Web of Science API.
    depth (int): The maximum depth to fetch references.
    visited_dois (set): A set to keep track of visited DOIs to avoid re-fetching.

    Returns:
    list: A list of processed paper data, each containing metadata and references.
    """
    
    # Queue to hold papers at each level (starting with initial papers)
    queue = deque([(paper, 0) for paper in papers])  # (paper, current_depth)
    processed_papers = []

    current_depth = 0
    while queue and current_depth <= depth:
        # Filter out papers to process at the current depth
        papers_at_current_depth = [p for p in queue if p[1] == current_depth]
        if not papers_at_current_depth:
            current_depth += 1
            continue

        # Use tqdm to show progress for the current depth
        progress_bar = tqdm(papers_at_current_depth, desc=f"Processing papers at depth {current_depth}", leave=True)

        for paper, _ in progress_bar:
            queue.popleft()  # Remove the paper from the queue

            # Extract DOI based on whether it's a dict or str
            if isinstance(paper, dict):
                paper_doi = paper.get('doi')
            else:
                paper_doi = paper

            # If we haven't visited this DOI yet
            if paper_doi and paper_doi not in visited_dois:
                visited_dois.add(paper_doi)

                # Fetch metadata and UID for the paper
                metadata, uid = fetch_metadata_uid_using_doi(paper_doi, api_key)
                if uid:
                    filtered_metadata = extract_relevant_metadata(metadata)

                    # If we are at max depth, don't fetch references
                    if current_depth >= depth:
                        references = []
                    else:
                        # Fetch references using UID
                        references_data = fetch_references_using_uid(uid, api_key)
                        
                        # Extract DOIs of references and add them to the queue for the next level (depth + 1)
                        # references = []
                        if references_data:
                            reference_dois = extract_dois(references_data)
                            references = reference_dois
                            for ref_doi in reference_dois:
                                queue.append((ref_doi, current_depth + 1))  # Add references to queue for next depth level

                    processed_papers.append({
                        'doi': paper_doi,
                        'metadata': filtered_metadata,
                        'references': references
                    })

        # Close the progress bar for the current depth
        progress_bar.close()

        # Increment depth for the next batch
        current_depth += 1

    return processed_papers



def display_statistics(all_papers_data):
    
    """
    Processes a collection of papers to compute and display statistics.
    
    Parameters:
    - all_papers_data (list): A list of dictionaries where each dictionary represents a paper.
      Each paper may contain metadata and references to other papers.
    
    Returns:
    - None: This function prints the computed statistics directly.
    """
    
    total_papers = 0
    total_references = 0
    doc_type_counts = {'Article': 0, 'Book': 0, 'Other': 0}
    depth_counts = {}

    def traverse_papers(papers, current_depth):
        
        """
        Recursively traverses the papers and their references to update counts for 
        total papers, total references, document types, and depth levels.
        
        Parameters:
        - papers (list): A list of dictionaries representing the papers at the current level.
        - current_depth (int): The current depth in the reference hierarchy.
        
        Returns:
        - None: Updates the statistics in place.
        """
        
        nonlocal total_papers, total_references
        if current_depth not in depth_counts:
            depth_counts[current_depth] = 0

        for paper in papers:
            total_papers += 1
            depth_counts[current_depth] += 1

            metadata = paper.get('metadata', {})
            references = paper.get('references', [])
            total_references += len(references)

            doc_types = metadata.get('document_type', [])
            if 'Article' in doc_types:
                doc_type_counts['Article'] += 1
            elif 'Book' in doc_types:
                doc_type_counts['Book'] += 1
            else:
                doc_type_counts['Other'] += 1

            traverse_papers(references, current_depth + 1)

    traverse_papers(all_papers_data, current_depth=0)


    print("\nStatistics:")
    print(f"Total papers processed: {total_papers}")
    
    for depth, count in depth_counts.items():
        print(f"Number of papers processed at depth {depth}: {count}")
        
    print(f"Number of articles: {doc_type_counts['Article']}")
    print(f"Number of books: {doc_type_counts['Book']}")
    print(f"Documents with Other document types: {doc_type_counts['Other']}")
    


def main(visited_dois=set()):

    """
    Main function to load seed papers from a BibTeX file, process them to fetch metadata and references,
    and save the results to a JSON file.
    """

    with open('seedPapers.bib') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    
    papers = bib_database.entries

    api_key = 'your-api-key'
    depth = 3
    

    folder_path = 'social_unrest_metadata_depth3_bfs'
    os.makedirs(folder_path, exist_ok=True)

    for i in range(len(papers)): # len(papers)
        seed_paper_data = process_papers(papers[i:i+1], api_key, depth, visited_dois) ######
        file_name = os.path.join(folder_path, f"seed_paper_{i+1}.json")
        with open(file_name, 'w') as f:
            json.dump(seed_paper_data, f, indent=4)
        print(f"Seed Paper : {i+1}/16")
        display_statistics(seed_paper_data)
        
    return visited_dois
        

if __name__ == "__main__":
    visited_dois_set = main()
    # print(len(visited_dois_set))
    # visited_dois_set = main(visited_dois_set)
    # print(len(visited_dois_set))