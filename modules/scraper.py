"""
Web scraping module for extracting main content from webpages
Handles various HTML structures and cleans text for readability analysis
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
import re
import html
from typing import Dict, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_webpage(url: str, timeout: int = 30) -> Dict:
    """
    Extract main content from a webpage.
    
    Args:
        url: URL to scrape
        timeout: Request timeout in seconds
    
    Returns:
        Dictionary with url, content, word_count, status, error_msg
    """
    result = {
        'url': url,
        'content': None,
        'word_count': 0,
        'status': 'success',
        'error_msg': None
    }
    
    try:
        # Request with custom user agent
        headers = {'User-Agent': config.USER_AGENT}
        response = requests.get(url, timeout=timeout, headers=headers, allow_redirects=True)
        
        if response.status_code != 200:
            result['status'] = f'http_error_{response.status_code}'
            result['error_msg'] = f"HTTP {response.status_code}"
            return result
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract main content using multiple strategies
        content = extract_main_content(soup)
        
        if not content:
            result['status'] = 'extraction_failed'
            result['error_msg'] = 'Could not extract content'
            return result
        
        # Clean the text
        cleaned_content = clean_text(content)
        
        # Validate content quality
        is_valid, issues = validate_content(cleaned_content)
        
        if not is_valid:
            result['status'] = 'insufficient_text'
            result['error_msg'] = '; '.join(issues)
            result['content'] = cleaned_content  # Still return it for inspection
            result['word_count'] = len(cleaned_content.split())
            return result
        
        result['content'] = cleaned_content
        result['word_count'] = len(cleaned_content.split())
        
    except requests.Timeout:
        result['status'] = 'timeout'
        result['error_msg'] = 'Request timeout'
    except requests.RequestException as e:
        result['status'] = 'request_error'
        result['error_msg'] = str(e)
    except Exception as e:
        result['status'] = 'error'
        result['error_msg'] = str(e)
        logger.error(f"Error scraping {url}: {e}")
    
    return result


def extract_main_content(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract main text content from HTML using multiple strategies.
    
    Args:
        soup: BeautifulSoup object
    
    Returns:
        Extracted text or None
    """
    # Remove unwanted elements
    for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                        'aside', 'iframe', 'noscript']):
        element.decompose()
    
    # Strategy 1: Try <article> tag
    article = soup.find('article')
    if article:
        text = article.get_text(separator=' ', strip=True)
        if len(text.split()) > config.MIN_WORD_COUNT:
            return text
    
    # Strategy 2: Try <main> tag
    main = soup.find('main')
    if main:
        text = main.get_text(separator=' ', strip=True)
        if len(text.split()) > config.MIN_WORD_COUNT:
            return text
    
    # Strategy 3: Look for content-related classes/ids
    content_indicators = [
        'content', 'article', 'post', 'entry', 'text',
        'main', 'body', 'story', 'page-content'
    ]
    
    for indicator in content_indicators:
        # Try as class
        elements = soup.find_all(class_=re.compile(indicator, re.I))
        for elem in elements:
            text = elem.get_text(separator=' ', strip=True)
            if len(text.split()) > config.MIN_WORD_COUNT:
                return text
        
        # Try as id
        elem = soup.find(id=re.compile(indicator, re.I))
        if elem:
            text = elem.get_text(separator=' ', strip=True)
            if len(text.split()) > config.MIN_WORD_COUNT:
                return text
    
    # Strategy 4: Get all paragraph text from body
    body = soup.find('body')
    if body:
        paragraphs = body.find_all('p')
        if paragraphs:
            text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            if len(text.split()) > config.MIN_WORD_COUNT:
                return text
    
    # Strategy 5: Last resort - all text from body
    if body:
        text = body.get_text(separator=' ', strip=True)
        return text if text else None
    
    return None


def clean_text(raw_text: str) -> str:
    """
    Clean and normalize extracted text.
    
    Args:
        raw_text: Raw extracted text
    
    Returns:
        Cleaned text
    """
    if not raw_text:
        return ""
    
    # Decode HTML entities
    text = html.unescape(raw_text)
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Normalize whitespace (multiple spaces to single space)
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s.,!?;:\-\(\)\'\"]+', '', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def validate_content(text: str) -> tuple:
    """
    Validate quality of extracted content.
    
    Args:
        text: Cleaned text
    
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    if not text:
        issues.append("Empty text")
        return False, issues
    
    words = text.split()
    word_count = len(words)
    
    # Check minimum word count (ONLY CRITICAL CHECK)
    if word_count < config.MIN_WORD_COUNT:
        issues.append(f"Text too short ({word_count} words)")
        return False, issues  # This is hard failure
    
    # Check maximum word count (likely scraping error)
    if word_count > config.MAX_WORD_COUNT:
        issues.append(f"Text too long ({word_count} words - likely error)")
        return False, issues  # This is hard failure
    
    # Check sentence structure (WARNING ONLY - NOT FATAL)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) < 3:  # Relaxed from 5 to 3
        logger.warning(f"Few sentences detected ({len(sentences)}) but proceeding")
    
    # Check for boilerplate phrases (WARNING ONLY - NOT FATAL)
    boilerplate_patterns = [
        'copyright', 'all rights reserved', 'terms of service',
        'privacy policy', 'cookie policy', 'accept cookies'
    ]
    boilerplate_count = sum(text.lower().count(pattern) for pattern in boilerplate_patterns)
    if boilerplate_count > 8:  # Relaxed from 5 to 8
        logger.warning(f"High boilerplate content detected ({boilerplate_count} instances) but proceeding")
    
    # If we got here, content is valid enough
    return True, []


def scrape_with_retry(url: str, max_attempts: int = 3) -> Dict:
    """
    Scrape with exponential backoff retry.
    
    Args:
        url: URL to scrape
        max_attempts: Maximum retry attempts
    
    Returns:
        Scraping result dictionary
    """
    for attempt in range(max_attempts):
        result = scrape_webpage(url)
        
        if result['status'] == 'success':
            return result
        
        # Retry on timeout or server errors
        if result['status'] in ['timeout', 'http_error_500', 'http_error_502', 'http_error_503']:
            if attempt < max_attempts - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retry {attempt + 1}/{max_attempts} for {url} in {wait_time}s")
                time.sleep(wait_time)
            else:
                logger.warning(f"Failed after {max_attempts} attempts: {url}")
        else:
            # Don't retry for other errors
            break
    
    return result


if __name__ == "__main__":
    # Test the scraper
    test_urls = [
        "https://www.mayoclinic.org/diseases-conditions/high-blood-pressure/symptoms-causes/syc-20373410",
        "https://www.cdc.gov/bloodpressure/about.htm",
    ]
    
    for url in test_urls:
        print(f"\nScraping: {url}")
        result = scrape_webpage(url)
        print(f"Status: {result['status']}")
        print(f"Word count: {result['word_count']}")
        if result['content']:
            print(f"Content preview: {result['content'][:200]}...")
