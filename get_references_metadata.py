import json
import requests
import bibtexparser

def fetch_metadata_uid_using_doi(doi, api_key):
    
    """
    Fetches metadata and UID for a given DOI using the Web of Science API.

    Parameters:
    doi (str): The DOI of the paper to fetch metadata for.
    api_key (str): The API key for authenticating with the Web of Science API.

    Returns:
    The metadata JSON response and the UID string.
    """

    url = f"https://api.clarivate.com/api/wos?databaseId=WOK&usrQuery=DO=({doi})"
    headers = {
        'X-ApiKey': api_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f'\nReceiving response for DOI {doi}:\n{response.json()}')
        uid = ''
        if response.json()['QueryResult']['RecordsFound'] > 0:
            uid = response.json()['Data']['Records']['records']['REC'][0]['UID']
            print('UID : ', uid.replace(':', '%3A'))
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
    dictionary: A dictionary of references. 
    List of references can be accessed using the 'Data' key in the Dictionary.

    Notes:
    API can handle only 100 references per query (pagination). 'count=100'
    'first_index' field is used to tackle pagination.
    """

    all_references = {'Data':[], 'QueryResult':{}}
    first_index = 1
    count = 100

    while True:
        url = f"https://api.clarivate.com/api/wos/references?databaseId=WOK&uniqueId={uid}&count={count}&firstRecord={first_index}"
        headers = {
            'X-ApiKey': api_key
        }
        response = requests.get(url, headers=headers)
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
    print(f'\nReceiving references for UID {uid}:\n{all_references}\n')
    return all_references


def extract_dois(references):

    """
    Extracts DOIs from a dict of references.

    Parameters:
    references (dictionary): A dict of reference dictionaries. References can be accessed using the 'Data' key in the dict.

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


def process_papers(papers, api_key, depth, visited_dois, current_depth=0):

    """
    Processes a list of papers to fetch their metadata and references recursively up to a specified depth.

    Parameters:
    papers (list): A list of paper dictionaries or DOIs.
    api_key (str): The API key for authenticating with the Web of Science API.
    depth (int): The maximum depth to fetch references recursively.
    visited_dois (set): A set to keep track of visited DOIs to avoid re-fetching.
    current_depth (int, optional): The current recursion depth. Default is 0.

    Returns:
    list of dictionaries: A list of processed paper data, each element is a dictionary containing metadata and references.
    """

    if current_depth > depth:
        return []

    processed_papers = []

    p_counter = 0

    for paper in papers:
        p_counter += 1
        print('Counter : ', p_counter, '/', len(papers))
        if isinstance(paper, dict):
            paper_doi = paper.get('doi')
        else:
            paper_doi = paper
        
        if paper_doi and paper_doi not in visited_dois: 
            visited_dois.add(paper_doi) 
            metadata, uid = fetch_metadata_uid_using_doi(paper_doi, api_key)
            if uid:
                references_data = fetch_references_using_uid(uid, api_key)
                if references_data:
                    reference_dois = extract_dois(references_data)
                    references = process_papers(reference_dois, api_key, depth, visited_dois, current_depth + 1) 
                    processed_papers.append({
                        'doi': paper_doi,
                        'metadata': metadata,
                        'references': references
                    })

    return processed_papers


def main():

    """
    Main function to load seed papers from a BibTeX file, process them to fetch metadata, full text, and references,
    and save the results to a JSON file.
    """

    with open('seedPapers.bib') as bibtex_file:
        bib_database = bibtexparser.load(bibtex_file)
    
    papers = bib_database.entries

    api_key = 'your-api-key'
    depth = 1
    visited_dois = set() 

    all_papers_data = process_papers(papers, api_key, depth, visited_dois) 

    with open('all_papers_data.json', 'w') as f:
        json.dump(all_papers_data, f, indent=4)
        

if __name__ == "__main__":
    main()
