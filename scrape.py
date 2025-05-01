import requests
import os
from pprint import pprint
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import logging # Added for better error logging

load_dotenv()
logging.basicConfig(level=logging.INFO) # Basic logging setup

USERNAME = os.getenv("OX_USERNAME")
PASSWORD = os.getenv("OX_PASSWORD")
API_URL = "https://realtime.oxylabs.io/v1/queries"

# --- NEW FUNCTION for Google Search ---
def search_google(query, update_status=None):
    """
    Performs a Google search using  SERP API and returns organic results.

    Parameters:
      query (str): The search topic/query.
      update_status (callable): Optional callback to update status.

    Returns:
      list: A list of dictionaries [{'title': '...', 'link': '...'}, ...] or empty list on error/no results.
    """
    if not USERNAME or not PASSWORD:
        logging.error(" credentials (OX_USERNAME, OX_PASSWORD) not found in environment.")
        if update_status:
            update_status("Error: API credentials missing.")
        return []

    if update_status:
        update_status(f"Searching Google for: '{query}'...")

    payload = {
        'source': 'google_search', # Use the SERP source
        'query': query,
        'geo_location': 'India', # Or make this configurable
        'user_agent_type': 'desktop',
        'parse': True # Request parsed results if available
    }

    try:
        if update_status:
            update_status("Getting relevent link about topic...")
        response = requests.post(API_URL, auth=(USERNAME, PASSWORD), json=payload, timeout=120) # Added timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        if update_status:
            update_status("Received search results.")

        result = response.json()
        
        organic_results = []
        search_results = result.get("results", [])
        if search_results:
            content = search_results[0].get("content", {})
            # Try finding 'organic' directly under 'results' first
            organic_data = content.get("results", {}).get("organic")
            # If not found, try finding 'organic' directly under 'content'
            if not organic_data:
                organic_data = content.get("organic")

            if organic_data and isinstance(organic_data, list):
                for item in organic_data:
                    # Ensure item is a dictionary and has 'title' and 'url'/'link'
                    if isinstance(item, dict) and 'title' in item and ('url' in item or 'link' in item):
                         # Prefer 'url', fallback to 'link'
                        link = item.get('url', item.get('link'))
                        if link: # Make sure link is not None or empty
                           organic_results.append({
                               'title': item.get('title', 'No Title'),
                               'link': link
                           })

        if not organic_results:
             if update_status: update_status(f"No organic results found for '{query}'.")
             logging.warning(f"No organic results extracted for query: {query}")
        else:
             if update_status: update_status(f"Found {len(organic_results)} potential links.")

        return organic_results

    except requests.exceptions.RequestException as e:
        logging.error(f"Error during SERP API request: {e}")
        if update_status:
            update_status(f"Error performing search: {e}")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred during search: {e}")
        if update_status:
            update_status(f"An unexpected error occurred during search.")
        return []


# --- EXISTING FUNCTIONS (mostly unchanged) ---

def scrape_website(website_url, update_status=None): # Renamed 'website' to 'website_url' for clarity
    """
    Scrape the website using the Web Scraper API and return the HTML source.

    Parameters:
      website_url (str): URL of the website to scrape.
      update_status (callable): Optional callback to update status.
    """
    if not USERNAME or not PASSWORD:
        logging.error(" credentials (OX_USERNAME, OX_PASSWORD) not found.")
        if update_status:
            update_status("Error: API credentials missing.")
        return ""

    if update_status:
        update_status(f"Preparing to scrape: {website_url}...")

    payload = {
        'source': 'universal', # Use the Web Scraper source
        'geo_location': 'India',
        'user_agent_type': 'desktop_firefox',
        'render': 'html',
        'url': website_url # Use the passed URL
    }

    try:
        if update_status:
            update_status("Scraping requested link ...")
        response = requests.post(API_URL, auth=(USERNAME, PASSWORD), json=payload, timeout=180) # Longer timeout for rendering
        response.raise_for_status()

        if update_status:
            update_status("Received scraped content.")

        result = response.json()
        # pprint(result) # Uncomment for debugging raw scraping response

        html_content = ""
        if "results" in result and isinstance(result["results"], list) and len(result["results"]) > 0:
            content_data = result["results"][0].get("content", "")
            # Handle cases where content might be nested
            if isinstance(content_data, dict):
                html_content = content_data.get("content", "") # Example nesting
            elif isinstance(content_data, str):
                html_content = content_data

        if not html_content:
             logging.warning(f"No HTML content extracted from scraping {website_url}")
             if update_status: update_status("Warning: Could not extract HTML content.")

        return html_content

    except requests.exceptions.RequestException as e:
        logging.error(f"Error during Web Scraping request for {website_url}: {e}")
        if update_status:
            update_status(f"Error scraping URL: {e}")
        return ""
    except Exception as e:
        logging.error(f"An unexpected error occurred during scraping {website_url}: {e}")
        if update_status:
            update_status(f"An unexpected error occurred during scraping.")
        return ""


def extract_body_content(html_content, update_status=None):
    """Extracts and returns the string representation of the <body> tag."""
    if not html_content: return ""
    if update_status:
        update_status("Extracting main content from HTML...")
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        body = soup.body
        return str(body) if body else ""
    except Exception as e:
        logging.error(f"Error extracting body content: {e}")
        if update_status: update_status("Error processing HTML structure.")
        return ""


def clean_body_content(body_content, update_status=None):
    """Removes scripts, styles, and excessive whitespace."""
    if not body_content: return ""
    if update_status:
        update_status("Cleaning extracted content...")
    try:
        soup = BeautifulSoup(body_content, "html.parser")
        for element in soup(["script", "style", "header", "footer", "nav", "aside"]): # Remove more non-essential tags
            element.extract()

        # Get text, remove leading/trailing whitespace from each line, join non-empty lines
        text = soup.get_text(separator='\n', strip=True)
        lines = [line for line in (l.strip() for l in text.splitlines()) if line] # More robust cleaning
        cleaned_text = "\n".join(lines)

        # Limit length slightly defensively before splitting
        MAX_CLEAN_LEN = 500000 # Example limit
        if len(cleaned_text) > MAX_CLEAN_LEN:
            logging.warning("Cleaned content exceeds limit, truncating.")
            cleaned_text = cleaned_text[:MAX_CLEAN_LEN]
            if update_status: update_status("Warning: Cleaned content was very large, truncated.")

        return cleaned_text
    except Exception as e:
        logging.error(f"Error cleaning body content: {e}")
        if update_status: update_status("Error during content cleaning.")
        return ""


def split_dom_content(dom_content, max_length=15000):
    """Splits cleaned text content into chunks."""
    if not dom_content: return []
    return [dom_content[i : i + max_length] for i in range(0, len(dom_content), max_length)]