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
        return response.json(), uid.replace(':', '%3A')
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
            doi = doi.replace('/', '%2F').replace('.', '%2E').replace('-', '%2D')
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
    dict: A dictionary of all the relavant metadata extracted from the article.
    """
    
    try:
        record = metadata['Data']['Records']['records']['REC'][0]
        wos_id = record.get('UID', '')
        identifiers = record.get('dynamic_data', {}).get('cluster_related', {}).get('identifiers', {}).get('identifier', [])
        doi = ''

        if isinstance(identifiers, list):
            doi = next((id_info['value'] for id_info in identifiers if isinstance(id_info, dict) and id_info.get('type') == 'doi'), '')
        elif isinstance(identifiers, dict) and identifiers.get('type') == 'doi':
            doi = identifiers.get('value', '')

        title = next((title_info['content'] for title_info in record.get('static_data', {}).get('summary', {}).get('titles', {}).get('title', []) if title_info['type'] == 'item'), '')

        names_data = record.get('static_data', {}).get('summary', {}).get('names', {}).get('name', [])
        authors = []
        if isinstance(names_data, list):
            authors = [author['full_name'] for author in names_data if author['role'] == 'author']
        elif isinstance(names_data, dict) and names_data.get('role') == 'author':
            authors = [names_data.get('full_name', '')]

        abstract_data = record.get('static_data', {}).get('fullrecord_metadata', {}).get('abstracts', {}).get('abstract', {})
        abstract = ''
        if isinstance(abstract_data, dict):
            abstract = abstract_data.get('abstract_text', {}).get('p', '')
        elif isinstance(abstract_data, list):
            for abs_item in abstract_data:
                if isinstance(abs_item, dict):
                    abstract = abs_item.get('abstract_text', {}).get('p', '')
                    if abstract:
                        break

        keywords = record.get('static_data', {}).get('fullrecord_metadata', {}).get('keywords', {}).get('keyword', [])
        doc_type = record.get('static_data', {}).get('summary', {}).get('doctypes', {}).get('doctype', [])

        publisher_info = record.get('static_data', {}).get('summary', {}).get('publishers', {}).get('publisher', {})
        publisher = ''
        if publisher_info:
            publisher = publisher_info.get('names', {}).get('name', {}).get('full_name', '')

        pub_info = record.get('static_data', {}).get('summary', {}).get('pub_info', {})
        pub_year = pub_info.get('pubyear', '')
        pub_date = pub_info.get('coverdate', '')

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
    except (KeyError, IndexError):
        # Return empty fields if the expected data structure is not found
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
    

def process_papers(papers, api_key, depth, visited_dois, current_depth=0): ######

    """
    Processes a list of papers to fetch their metadata and references recursively up to a specified depth.

    Parameters:
    papers (list): A list of paper dictionaries or DOIs.
    api_key (str): The API key for authenticating with the Web of Science API.
    depth (int): The maximum depth to fetch references recursively.
    visited_dois (set): A set to keep track of visited DOIs to avoid re-fetching.
    current_depth (int, optional): The current recursion depth. Default is 0.

    Returns:
    list: A list of processed paper data, each containing metadata, full text, and references.
    """

    if current_depth > depth:
        return []

    processed_papers = []
    # p_counter = 0
    progress_bar = tqdm(papers, desc=f"Processing papers at depth {current_depth}", leave=False)

    for paper in progress_bar:
        # p_counter += 1
        # print('Counter : ', p_counter, '/', len(papers))
        if isinstance(paper, dict):
            paper_doi = paper.get('doi')
        else:
            paper_doi = paper
        
        if paper_doi:# and paper_doi not in visited_dois:  ######
            # visited_dois.add(paper_doi) ######
            metadata, uid = fetch_metadata_uid_using_doi(paper_doi, api_key)
            if uid:
                filtered_metadata = extract_relevant_metadata(metadata)
                if current_depth + 1 > depth:
                    references = []
                else:
                    # print(current_depth)
                    # print('here')
                    references_data = fetch_references_using_uid(uid, api_key)
                    if references_data:
                        reference_dois = extract_dois(references_data)
                        references = process_papers(reference_dois, api_key, depth, visited_dois, current_depth + 1) ######
                processed_papers.append({
                    'doi': paper_doi,
                    'metadata': filtered_metadata,
                    'references': references
                })

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
    

def main():

    """
    Main function to load seed papers from a BibTeX file, process them to fetch metadata and references,
    and save the results to a JSON file.
    """

    with open('seedPapers.bib') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    
    papers = bib_database.entries

    api_key = 'your-api-key'
    depth = 2
    visited_dois = set() ######

    folder_path = 'social_unrest_metadata_1'
    os.makedirs(folder_path, exist_ok=True)

    for i in range(0,16): # len(papers)
        seed_paper_data = process_papers(papers[i:i+1], api_key, depth, visited_dois) ######
        file_name = os.path.join(folder_path, f"seed_paper_{i+1}.json")
        with open(file_name, 'w') as f:
            json.dump(seed_paper_data, f, indent=4)
        print(f"Seed Paper : {i+1}/16")
        display_statistics(seed_paper_data)
        

if __name__ == "__main__":
    main()