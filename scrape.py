import requests
import os
from pprint import pprint
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

def scrape_website(website, update_status=None):
    """
    Scrape the website using the Oxylabs API and return the HTML source.
    
    Parameters:
      website (str): URL of the website to scrape.
      update_status (callable): Optional callback to update status.
    """
    if update_status:
        update_status("Connecting to Oxylabs API for scraping...")

    # Set up the payload using the provided API template.
    payload = {
        'source': 'universal',
        'geo_location': 'India',
        'user_agent_type': 'desktop_firefox',
        'render': 'html',
        'url': website
    }
    
    # Get authentication credentials from environment variables or defaults.
    USERNAME = os.getenv("OX_USERNAME")
    PASSWORD = os.getenv("OX_PASSWORD")
    api_url = "https://realtime.oxylabs.io/v1/queries"
    
    if update_status:
        update_status("Sending request to Oxylabs API...")
    response = requests.post(api_url, auth=(USERNAME, PASSWORD), json=payload)
    
    if update_status:
        update_status("Received response from Oxylabs API.")
    
    result = response.json()
    print(result)
    if update_status:
        update_status("Processing the API response...")
    
    # Extract HTML content from the JSON response.
    html_content = ""
    if "results" in result and isinstance(result["results"], list) and len(result["results"]) > 0:
        # Use the "content" key from the first result.
        html_content = result["results"][0].get("content", "")
    else:
        html_content = ""
    
    if update_status:
        update_status("Scraping completed.")
    
    return html_content

def extract_body_content(html_content, update_status=None):
    """
    Extract the <body> portion of the HTML.
    
    Parameters:
      html_content (str): The full HTML source.
      update_status (callable): Optional callback for status updates.
    """
    if update_status:
        update_status("Extracting body from HTML content...")
    soup = BeautifulSoup(html_content, "html.parser")
    body_content = soup.body
    return str(body_content) if body_content else ""

def clean_body_content(body_content, update_status=None):
    """
    Clean the HTML by removing script and style tags and extra whitespace.
    
    Parameters:
      body_content (str): HTML body content.
      update_status (callable): Optional callback for status updates.
    """
    if update_status:
        update_status("Cleaning up DOM content...")
    soup = BeautifulSoup(body_content, "html.parser")
    for script_or_style in soup(["script", "style"]):
        script_or_style.extract()
    cleaned_content = soup.get_text(separator="\n")
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )
    return cleaned_content

def split_dom_content(dom_content, max_length=6000):
    """
    Split DOM content into chunks (default max length 6000 characters).
    """
    return [dom_content[i : i + max_length] for i in range(0, len(dom_content), max_length)]
