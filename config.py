# Configuration file for Medical Readability Analyzer

import streamlit as st

# Google API Configuration
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
SEARCH_ENGINE_ID = st.secrets.get("SEARCH_ENGINE_ID", "")

# SerpAPI Configuration (For 100+ results)
SERPAPI_KEY = st.secrets.get("SERPAPI_KEY", "")

# Scraping Configuration
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_DELAY = 1  # Seconds between requests

# Classification Configuration
INSTITUTIONAL_DOMAINS = [
    '.gov', '.gov.uk', '.gov.au', '.gov.ca',
    '.edu', '.ac.uk', '.ac.au', '.edu.au',
    '.nhs.uk', '.nhs.net',
    'who.int', 'cdc.gov', 'nih.gov',
    'mayoclinic.org', 'clevelandclinic.org',
    'hopkinsmedicine.org', 'webmd.com',
    'healthline.com', 'medlineplus.gov',
]

INSTITUTIONAL_PATTERNS = [
    '/government/', '/health/official/',
    '/public-health/', '/medical-center/',
    'university', 'college', 'hospital',
]

INSTITUTIONAL_KEYWORDS = [
    'National Institutes', 'Centers for Disease',
    'National Health Service', 'Mayo Clinic',
    'Cleveland Clinic', 'Johns Hopkins',
    'CDC', 'NIH', 'NHS', 'WHO',
]

CONFIDENCE_THRESHOLD = 3

# Analysis Configuration
MIN_WORD_COUNT = 50
MAX_WORD_COUNT = 50000
SIGNIFICANCE_LEVEL = 0.05

# Export Configuration
EXCEL_ENGINE = 'openpyxl'
FIGURE_DPI = 300
FIGURE_FORMAT = 'png'

# Default settings
DEFAULT_NUM_RESULTS = 100
