"""
Source classification module
Classifies URLs as Institutional or Private based on domain, URL patterns, and keywords
"""

import logging
from typing import Tuple
from urllib.parse import urlparse
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def classify_source(url: str, page_title: str = "", domain: str = "") -> Tuple[str, int]:
    """
    Classify a source as Institutional or Private.
    
    Args:
        url: Full URL
        page_title: Page title (optional)
        domain: Domain name (optional, will be extracted if not provided)
    
    Returns:
        Tuple of (classification, confidence_score)
        classification: "Institutional" or "Private"
        confidence_score: 0-6 scale
    """
    confidence = 0
    
    # Extract domain if not provided
    if not domain:
        domain = extract_domain_from_url(url)
    
    url_lower = url.lower()
    domain_lower = domain.lower()
    title_lower = page_title.lower() if page_title else ""
    
    # Level 1: Check domain suffix (HIGH CONFIDENCE +3)
    for inst_domain in config.INSTITUTIONAL_DOMAINS:
        if domain_lower.endswith(inst_domain) or inst_domain in domain_lower:
            confidence += 3
            logger.debug(f"Domain match: {inst_domain} in {domain}")
            break
    
    # Level 2: Check URL patterns (MEDIUM CONFIDENCE +2)
    for pattern in config.INSTITUTIONAL_PATTERNS:
        if pattern.lower() in url_lower:
            confidence += 2
            logger.debug(f"URL pattern match: {pattern}")
            break
    
    # Level 3: Check title for institutional keywords (LOW CONFIDENCE +1)
    if title_lower:
        for keyword in config.INSTITUTIONAL_KEYWORDS:
            if keyword.lower() in title_lower:
                confidence += 1
                logger.debug(f"Title keyword match: {keyword}")
                break
    
    # Classification decision
    if confidence >= config.CONFIDENCE_THRESHOLD:
        classification = "Institutional"
    else:
        classification = "Private"
    
    logger.info(f"Classified {domain} as {classification} (confidence: {confidence})")
    
    return classification, confidence


def extract_domain_from_url(url: str) -> str:
    """
    Extract clean domain from URL.
    
    Args:
        url: Full URL
    
    Returns:
        Domain without www prefix
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Remove www. prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain
    except Exception as e:
        logger.error(f"Error extracting domain from {url}: {e}")
        return url


def batch_classify(urls_data: list) -> list:
    """
    Classify multiple URLs at once.
    
    Args:
        urls_data: List of dictionaries with 'url', 'title' keys
    
    Returns:
        Same list with added 'source_type' and 'confidence' keys
    """
    for data in urls_data:
        classification, confidence = classify_source(
            data.get('url', ''),
            data.get('title', ''),
            data.get('domain', '')
        )
        data['source_type'] = classification
        data['classification_confidence'] = confidence
    
    return urls_data


def get_ambiguous_classifications(urls_data: list, threshold: int = 2) -> list:
    """
    Get URLs with low confidence classifications that may need manual review.
    
    Args:
        urls_data: List of classified URL data
        threshold: Confidence threshold (classifications below this are ambiguous)
    
    Returns:
        List of ambiguous classifications
    """
    ambiguous = []
    
    for data in urls_data:
        confidence = data.get('classification_confidence', 0)
        if confidence <= threshold and confidence > 0:
            ambiguous.append({
                'url': data.get('url'),
                'domain': data.get('domain', extract_domain_from_url(data.get('url', ''))),
                'classification': data.get('source_type'),
                'confidence': confidence
            })
    
    return ambiguous


def update_institutional_domains(new_domains: list):
    """
    Add new domains to institutional list (for user corrections).
    
    Args:
        new_domains: List of domain strings to add
    """
    # This would update a persistent configuration
    # For now, just log the update
    logger.info(f"Would add {len(new_domains)} domains to institutional list")
    for domain in new_domains:
        logger.info(f"  - {domain}")


def analyze_classification_distribution(urls_data: list) -> dict:
    """
    Analyze distribution of classifications.
    
    Args:
        urls_data: List of classified URL data
    
    Returns:
        Dictionary with classification statistics
    """
    total = len(urls_data)
    institutional = sum(1 for d in urls_data if d.get('source_type') == 'Institutional')
    private = sum(1 for d in urls_data if d.get('source_type') == 'Private')
    
    # Confidence distribution
    confidences = [d.get('classification_confidence', 0) for d in urls_data]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    high_confidence = sum(1 for c in confidences if c >= 3)
    medium_confidence = sum(1 for c in confidences if 1 <= c < 3)
    low_confidence = sum(1 for c in confidences if c == 0)
    
    return {
        'total': total,
        'institutional': institutional,
        'private': private,
        'institutional_pct': (institutional / total * 100) if total > 0 else 0,
        'private_pct': (private / total * 100) if total > 0 else 0,
        'avg_confidence': avg_confidence,
        'high_confidence_count': high_confidence,
        'medium_confidence_count': medium_confidence,
        'low_confidence_count': low_confidence,
    }


if __name__ == "__main__":
    # Test the classifier
    test_urls = [
        {'url': 'https://www.nih.gov/health-information', 'title': 'NIH Health Info'},
        {'url': 'https://www.cdc.gov/coronavirus', 'title': 'CDC Coronavirus'},
        {'url': 'https://www.mayoclinic.org/diseases', 'title': 'Mayo Clinic'},
        {'url': 'https://www.healthline.com/health', 'title': 'Healthline'},
        {'url': 'https://www.webmd.com/hypertension', 'title': 'WebMD Hypertension'},
        {'url': 'https://www.health.harvard.edu/blog', 'title': 'Harvard Health'},
        {'url': 'https://www.medicalnewstoday.com', 'title': 'Medical News Today'},
    ]
    
    print("\nClassification Results:")
    print("-" * 80)
    
    for url_data in test_urls:
        classification, confidence = classify_source(url_data['url'], url_data['title'])
        domain = extract_domain_from_url(url_data['url'])
        print(f"{domain:40} {classification:15} Confidence: {confidence}")
    
    # Batch classification
    batch_results = batch_classify(test_urls)
    
    # Analyze distribution
    stats = analyze_classification_distribution(batch_results)
    print("\n" + "="* 80)
    print("Classification Statistics:")
    print(f"  Institutional: {stats['institutional']} ({stats['institutional_pct']:.1f}%)")
    print(f"  Private: {stats['private']} ({stats['private_pct']:.1f}%)")
    print(f"  Average Confidence: {stats['avg_confidence']:.2f}")
