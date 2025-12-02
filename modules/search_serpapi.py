"""
Alternative search module using SerpAPI
Provides actual Google search results (not limited like Custom Search API)
"""

import requests
import time
import logging
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SerpAPI configuration
SERPAPI_ENDPOINT = "https://serpapi.com/search"


def search_google_serpapi(keyword: str, api_key: str, num_results: int = 100) -> List[Dict]:
    """
    Search Google using SerpAPI for real Google results.
    
    Args:
        keyword: Search term
        api_key: SerpAPI key
        num_results: Number of results to retrieve
    
    Returns:
        List of result dictionaries
    """
    logger.info(f"Starting SerpAPI search for: {keyword}")
    
    results = []
    page = 0
    results_per_page = 10
    
    while len(results) < num_results and page < 10:  # Max 10 pages = 100 results
        try:
            params = {
                "q": keyword,
                "api_key": api_key,
                "num": 10,  # Request 10 per page
                "start": page * 10,
                "engine": "google"
            }
            
            logger.info(f"Fetching page {page + 1} (results {page * 10 + 1}-{(page + 1) * 10})...")
            
            response = requests.get(SERPAPI_ENDPOINT, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"SerpAPI error: HTTP {response.status_code}")
                # Check for error message
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        logger.error(f"  Error: {error_data['error']}")
                except:
                    pass
                break
            
            data = response.json()
            
            # Check for API errors
            if 'error' in data:
                logger.error(f"SerpAPI returned error: {data['error']}")
                break
            
            # Extract organic results
            if 'organic_results' in data:
                page_results = len(data['organic_results'])
                
                for item in data['organic_results']:
                    result = {
                        'url': item.get('link', ''),
                        'title': item.get('title', ''),
                        'snippet': item.get('snippet', ''),
                        'rank': len(results) + 1,
                    }
                    results.append(result)
                
                logger.info(f"  Added {page_results} results (total: {len(results)})")
                
                # Only stop if we got 0 results
                if page_results == 0:
                    logger.info("  No more results available from Google")
                    break
            else:
                logger.warning(f"  No organic_results - Response keys: {list(data.keys())[:5]}")
                # Still continue to next page - might be a fluke
            
            page += 1
            
            # Rate limiting - only if we're continuing
            if page < 10 and len(results) < num_results:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Error on page {page + 1}: {e}")
            # Continue to next page unless it's a critical error
            page += 1
            if page < 10:
                time.sleep(1)
    
    logger.info(f"SerpAPI search complete. Retrieved {len(results)} results.")
    return results


def search_google_fallback(keyword: str, num_results: int = 100) -> List[Dict]:
    """
    Fallback method: Manual URL construction for common medical sites.
    This creates a curated list when APIs fail.
    
    Args:
        keyword: Medical search term
        num_results: Target number
    
    Returns:
        List of constructed URLs from reliable medical sources
    """
    logger.warning("Using fallback search method - constructing URLs from known sources")
    
    # Common reliable medical information sources
    base_urls = [
        "https://www.mayoclinic.org/diseases-conditions/{term}",
        "https://www.cdc.gov/{term}",
        "https://www.nih.gov/health-information/{term}",
        "https://medlineplus.gov/{term}.html",
        "https://www.nhs.uk/conditions/{term}/",
        "https://www.healthline.com/health/{term}",
        "https://www.webmd.com/{term}",
        "https://www.clevelandclinic.org/health/{term}",
        "https://my.clevelandclinic.org/health/diseases/{term}",
        "https://www.hopkinsmedicine.org/health/conditions-and-diseases/{term}",
    ]
    
    # Format search term for URLs
    term_formatted = keyword.lower().replace(' ', '-')
    
    results = []
    for i, template in enumerate(base_urls):
        url = template.format(term=term_formatted)
        results.append({
            'url': url,
            'title': f"{keyword} - {template.split('/')[2]}",
            'snippet': f"Information about {keyword}",
            'rank': i + 1,
        })
    
    logger.info(f"Constructed {len(results)} URLs from known medical sources")
    return results


if __name__ == "__main__":
    # Test
    results = search_google_fallback("hypertension", 10)
    print(f"Fallback method created {len(results)} URLs:")
    for r in results[:5]:
        print(f"  - {r['url']}")
