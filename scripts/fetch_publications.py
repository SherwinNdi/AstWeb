"""
Fetch publications from Google Scholar and ORCID API and save to JSON.
This script is meant to run in GitLab CI before building the site.
"""

import json
import requests
from datetime import datetime
from pathlib import Path
import time

# Configuration
ORCID_ID = "0000-0001-6184-8484"  # Replace with your ORCID ID
GOOGLE_SCHOLAR_ID = "kGQy6cYAAAAJ"  # Replace with your Google Scholar ID (from your profile URL)
OUTPUT_FILE = Path(__file__).parent.parent / "src" / "data" / "publications.json"  # Absolute path from script location
USE_GOOGLE_SCHOLAR = False  # Set to False - Google Scholar blocks automated requests with CAPTCHA

def fetch_google_scholar_publications(scholar_id):
    """
    Fetch publications from Google Scholar using scholarly library.
    Install with: pip install scholarly
    """
    try:
        from scholarly import scholarly
        
        print("Fetching from Google Scholar (fast mode - basic info only)...")
        author = scholarly.search_author_id(scholar_id)
        author = scholarly.fill(author, sections=['publications'])
        
        publications = []
        total = len(author.get('publications', []))
        print(f"Found {total} publications, processing...")
        
        for idx, pub in enumerate(author['publications'], 1):
            # Don't fetch full details - use summary only (MUCH FASTER)
            bib = pub.get('bib', {})
            
            # Extract authors from summary
            authors = bib.get('author', 'Authors not available')
            if isinstance(authors, list):
                authors = ', '.join(authors)
            
            # Extract year
            year = bib.get('pub_year')
            if year:
                try:
                    year = int(year)
                except:
                    year = None
            
            publication = {
                'title': bib.get('title', 'Untitled'),
                'authors': authors,
                'journal': bib.get('venue', ''),
                'year': year,
                'doi': None,
                'url': pub.get('author_pub_id', ''),  # Use scholar URL
                'type': 'Research Article',
                'citations': pub.get('num_citations', 0)
            }
            
            if publication['title'] and publication['year']:
                publications.append(publication)
            
            # Progress indicator
            if idx % 20 == 0:
                print(f"  Processed {idx}/{total}...")
        
        print(f"✓ Fetched {len(publications)} publications from Google Scholar")
        return publications
        
    except ImportError:
        print("⚠ scholarly library not installed. Install with: pip install scholarly")
        print("Falling back to ORCID...")
        return None
    except Exception as e:
        print(f"Error fetching from Google Scholar: {e}")
        print("Falling back to ORCID...")
        return None


def fetch_orcid_publications(orcid_id):
    """
    Fetch publications from ORCID public API.
    """
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/works"
    headers = {
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from ORCID: {e}")
        return None

def fetch_work_details(orcid_id, put_code):
    """
    Fetch detailed information for a specific work.
    """
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/work/{put_code}"
    headers = {
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def fetch_crossref_details(doi):
    """
    Fetch complete publication details from CrossRef API using DOI.
    Returns full metadata including authors, abstract, citations, etc.
    """
    if not doi:
        return None
    
    url = f"https://api.crossref.org/works/{doi}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'message' not in data:
            return None
        
        message = data['message']
        result = {}
        
        # Extract authors
        if 'author' in message:
            authors = []
            for author in message['author']:
                given = author.get('given', '')
                family = author.get('family', '')
                if given and family:
                    authors.append(f"{given} {family}")
                elif family:
                    authors.append(family)
            result['authors'] = ', '.join(authors) if authors else None
        
        # Extract title
        if 'title' in message and message['title']:
            result['title'] = message['title'][0]
        
        # Extract journal/venue
        if 'container-title' in message and message['container-title']:
            result['journal'] = message['container-title'][0]
        
        # Extract year
        if 'published' in message:
            pub_date = message['published'].get('date-parts', [[]])[0]
            if pub_date:
                result['year'] = pub_date[0]
        elif 'published-print' in message:
            pub_date = message['published-print'].get('date-parts', [[]])[0]
            if pub_date:
                result['year'] = pub_date[0]
        elif 'published-online' in message:
            pub_date = message['published-online'].get('date-parts', [[]])[0]
            if pub_date:
                result['year'] = pub_date[0]
        
        # Extract DOI and URL
        result['doi'] = message.get('DOI')
        result['url'] = message.get('URL') or (f"https://doi.org/{result['doi']}" if result.get('doi') else None)
        
        # Extract type
        pub_type = message.get('type', '')
        type_mapping = {
            'journal-article': 'Research Article',
            'proceedings-article': 'Conference Paper',
            'book-chapter': 'Book Chapter',
            'book': 'Book',
            'dissertation': 'Dissertation',
        }
        result['type'] = type_mapping.get(pub_type, 'Publication')
        
        # Mark posted-content (preprints) so we can filter them out
        result['is_preprint'] = pub_type in ['posted-content', 'preprint']
        
        # Extract additional metadata
        result['abstract'] = message.get('abstract', '')
        result['citations'] = message.get('is-referenced-by-count', 0)
        result['publisher'] = message.get('publisher', '')
        result['volume'] = message.get('volume', '')
        result['issue'] = message.get('issue', '')
        result['pages'] = message.get('page', '')
        
        # Extract references count
        if 'reference' in message:
            result['references_count'] = len(message['reference'])
        
        return result
        
    except Exception as e:
        print(f"    ⚠ CrossRef error for DOI {doi}: {str(e)[:50]}")
        return None

def fetch_authors_from_crossref(doi):
    """
    Fetch author information from CrossRef API using DOI.
    """
    details = fetch_crossref_details(doi)
    return details.get('authors') if details else None

def extract_authors_from_work_detail(work_detail):
    """
    Extract authors from detailed work information.
    """
    if not work_detail:
        return None
    
    contributors_data = work_detail.get('contributors')
    if not contributors_data:
        return None
    
    contributors = contributors_data.get('contributor', [])
    if not contributors:
        return None
    
    authors = []
    for contributor in contributors:
        if not contributor:
            continue
        
        credit_name_data = contributor.get('credit-name')
        if credit_name_data:
            credit_name = credit_name_data.get('value')
            if credit_name:
                authors.append(credit_name)
    
    if authors:
        return ', '.join(authors)
    
    return None

def parse_orcid_works(data, orcid_id):
    """
    Parse ORCID works data and enrich with CrossRef details.
    """
    publications = []
    
    if not data or 'group' not in data:
        return publications
    
    total_works = len(data['group'])
    print(f"Processing {total_works} publications from ORCID...")
    print("Enriching with CrossRef data (this may take a few minutes)...\n")
    
    for idx, group in enumerate(data['group'], 1):
        work_summary_list = group.get('work-summary', [])
        if not work_summary_list:
            continue
        
        work_summary = work_summary_list[0]
        if not work_summary:
            continue
        
        # Get put-code for detailed fetch
        put_code = work_summary.get('put-code')
        
        # Extract basic info from ORCID
        title = work_summary.get('title', {}).get('title', {}).get('value', 'Untitled')
        
        # Get year
        pub_date = work_summary.get('publication-date')
        year = pub_date.get('year', {}).get('value') if pub_date else None
        
        # Get journal
        journal_title = work_summary.get('journal-title')
        if journal_title:
            journal_title = journal_title.get('value', '')
        else:
            journal_title = ''
        
        # Get type
        pub_type = work_summary.get('type', 'journal-article')
        
        # Skip preprints
        if pub_type == 'preprint':
            print(f"  [{idx}/{total_works}] Skipping preprint: {title[:60]}...")
            continue
        
        type_mapping = {
            'journal-article': 'Research Article',
            'conference-paper': 'Conference Paper',
            'book': 'Book',
            'book-chapter': 'Book Chapter',
            'dissertation': 'Dissertation',
        }
        formatted_type = type_mapping.get(pub_type, 'Publication')
        
        # Get DOI from ORCID
        external_ids = work_summary.get('external-ids', {})
        if external_ids:
            external_ids = external_ids.get('external-id', [])
        else:
            external_ids = []
        
        doi = None
        for ext_id in external_ids:
            if ext_id and ext_id.get('external-id-type') == 'doi':
                doi = ext_id.get('external-id-value')
                break
        
        # Get URL from ORCID
        url_data = work_summary.get('url')
        url = None
        if url_data:
            url = url_data.get('value')
        
        # Initialize publication with ORCID data
        publication = {
            'title': title,
            'authors': 'Authors not available',
            'journal': journal_title,
            'year': int(year) if year else None,
            'doi': doi,
            'url': url or (f"https://doi.org/{doi}" if doi else None),
            'type': formatted_type,
            'citations': 0,
            'abstract': '',
            'publisher': '',
            'volume': '',
            'issue': '',
            'pages': '',
            'references_count': 0,
        }
        
        # Fetch full details from CrossRef if DOI is available
        if doi:
            print(f"  [{idx}/{total_works}] Fetching CrossRef data for: {title[:60]}...")
            crossref_data = fetch_crossref_details(doi)
            
            if crossref_data:
                # Skip if CrossRef identifies this as a preprint
                if crossref_data.get('is_preprint', False):
                    print(f"    ⚠ Skipping preprint/posted-content")
                    continue
                
                # Merge CrossRef data (CrossRef takes priority for most fields)
                publication.update({
                    'title': crossref_data.get('title') or publication['title'],
                    'authors': crossref_data.get('authors') or publication['authors'],
                    'journal': crossref_data.get('journal') or crossref_data.get('publisher') or publication['journal'],
                    'year': crossref_data.get('year') or publication['year'],
                    'doi': crossref_data.get('doi') or publication['doi'],
                    'url': crossref_data.get('url') or publication['url'],
                    'type': crossref_data.get('type') or publication['type'],
                    'citations': crossref_data.get('citations', 0),
                    'abstract': crossref_data.get('abstract', ''),
                    'publisher': crossref_data.get('publisher', ''),
                    'volume': crossref_data.get('volume', ''),
                    'issue': crossref_data.get('issue', ''),
                    'pages': crossref_data.get('pages', ''),
                    'references_count': crossref_data.get('references_count', 0),
                })
                print(f"    ✓ Enriched with CrossRef data (Citations: {publication['citations']})")
            else:
                # Try to get authors from ORCID work details as fallback
                if put_code:
                    work_detail = fetch_work_details(orcid_id, put_code)
                    authors = extract_authors_from_work_detail(work_detail)
                    if authors:
                        publication['authors'] = authors
                print(f"    ⚠ No CrossRef data available")
            
            time.sleep(0.15)  # Be nice to the API (max ~7 requests/sec)
        else:
            # No DOI - try to get authors from ORCID work details
            if put_code:
                work_detail = fetch_work_details(orcid_id, put_code)
                authors = extract_authors_from_work_detail(work_detail)
                if authors:
                    publication['authors'] = authors
            print(f"  [{idx}/{total_works}] No DOI for: {title[:60]}...")
        
        # Only add if we have at least title and year
        if title and year:
            publications.append(publication)
    
    print(f"\n✓ Processed {len(publications)} publications with enriched data")
    return publications

def save_publications(publications, output_file):
    """
    Save publications to JSON file with metadata.
    """
    data = {
        'last_updated': datetime.utcnow().isoformat(),
        'count': len(publications),
        'publications': publications
    }
    
    # Ensure directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(publications)} publications to {output_file}")

def main():
    publications = None
    
    # Try Google Scholar first if enabled
    if USE_GOOGLE_SCHOLAR and GOOGLE_SCHOLAR_ID != "YOUR_SCHOLAR_ID":
        print(f"Fetching publications from Google Scholar: {GOOGLE_SCHOLAR_ID}")
        publications = fetch_google_scholar_publications(GOOGLE_SCHOLAR_ID)
    
    # Fallback to ORCID if Scholar fails or is disabled
    if not publications:
        print(f"Fetching publications from ORCID: {ORCID_ID}")
        data = fetch_orcid_publications(ORCID_ID)
        
        if not data:
            print("✗ Failed to fetch publications. Keeping existing file if present.")
            return 1
        
        publications = parse_orcid_works(data, ORCID_ID)
    
    if not publications:
        print("✗ No publications found.")
        return 1
    
    save_publications(publications, OUTPUT_FILE)
    print(f"✓ Successfully updated publications (Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    return 0

if __name__ == '__main__':
    exit(main())
