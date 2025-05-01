from flask import Flask, render_template, request, jsonify, redirect, url_for # Added redirect, url_for
# Import the new search function and the existing scrape functions
from scrape import search_google, scrape_website, extract_body_content, clean_body_content, split_dom_content
from parse import parse_with_gemini
import time
import logging
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = os.urandom(24) # Needed for flashing messages potentially, good practice

# Global dictionary for progress - consider Flask sessions for multi-user safety
progress_status = {"message": ""}
def update_progress(message):
    progress_status["message"] = message
    logging.info(f"Progress: {message}") # Log progress updates


@app.route("/", methods=["GET"])
def index():
    # Render the initial search page
    progress_status["message"] = "" # Clear status
    return render_template("index.html")

# --- NEW ROUTE for handling topic search ---
@app.route("/search", methods=["POST"]) # Changed endpoint name from /scrape to /search
def search_topic():
    topic = request.form.get("topic") # Changed from 'url' to 'topic'
    if not topic:
        progress_status["message"] = "Error: Please enter a topic to research."
        # Optionally redirect back to index with an error message (using flash)
        # flash("Error: Please enter a topic to research.")
        return redirect(url_for('index')) # Redirect back to the main page

    progress_status["message"] = f"Searching for '{topic}'..."

    # Call the new search function
    search_results = search_google(topic, update_status=update_progress)

    if not search_results:
        progress_status["message"] = f"No relevant links found for '{topic}'. Please try a different topic."
        # Render index again or a specific 'no results' page
        return render_template("index.html", error_message=progress_status["message"])

    # Render a new template to display the links
    progress_status["message"] = "Please select a link to scrape."
    return render_template("select_link.html", search_results=search_results, topic=topic)


# --- MODIFIED ROUTE to handle scraping *after* link selection ---
@app.route("/scrape", methods=["POST"]) # This route now receives selected_url
def scrape_selected_link():
    selected_url = request.form.get("selected_url") # Get URL chosen by user
    topic = request.form.get("topic") # Pass topic along if needed for context

    if not selected_url:
        progress_status["message"] = "Error: No link was selected."
        # Ideally, redirect back to selection page with an error
        # This might require passing the original search results back or re-searching
        # For simplicity, redirecting to index for now
        return redirect(url_for('index'))

    progress_status["message"] = f"Starting to scrape selected link: {selected_url}"

    # Use the original scraping/cleaning functions
    raw_dom = scrape_website(selected_url, update_status=update_progress)
    if not raw_dom:
        # Handle scraping failure
        progress_status["message"] = f"Failed to scrape content from {selected_url}. Please try another link."
        # Redirect or render an error page. Redirecting to index for simplicity.
        return render_template("index.html", error_message=progress_status["message"])

    body = extract_body_content(raw_dom, update_status=update_progress)
    cleaned = clean_body_content(body, update_status=update_progress)

    if not cleaned:
        progress_status["message"] = f"Could not extract or clean meaningful content from {selected_url}. Try another link."
        return render_template("index.html", error_message=progress_status["message"])


    progress_status["message"] = "Scraping and cleaning complete. Ready for parsing."
    # Pass the cleaned content to the parse template
    # Also pass the original topic and the scraped URL for context if needed
    return render_template("parse.html",
                           dom_content=cleaned,
                           parsed_result=None,
                           topic=topic,
                           scraped_url=selected_url)


# --- UNCHANGED ROUTE for parsing the scraped content ---
@app.route("/parse", methods=["POST"])
def parse():
    dom_content = request.form.get("dom_content")
    parse_description = request.form.get("parse_description") # User's question
    topic = request.form.get("topic") # Get context if needed
    scraped_url = request.form.get("scraped_url") # Get context if needed

    if not dom_content:
        progress_status["message"] = "Error: Scraped content is missing for parsing."
        # Redirect or show error - passing back to parse page with error
        return render_template("parse.html", error_message=progress_status["message"], topic=topic, scraped_url=scraped_url)

    if not parse_description:
        progress_status["message"] = "Error: Please enter a question about the content."
        # Re-render parse page with the content and an error message
        return render_template("parse.html", dom_content=dom_content, error_message=progress_status["message"], topic=topic, scraped_url=scraped_url)

    progress_status["message"] = f"Asking model about: '{parse_description}'..."

    dom_chunks = split_dom_content(dom_content)
    parsed_result = parse_with_gemini(dom_chunks, parse_description, update_status=update_progress)

    if not parsed_result:
         progress_status["message"] = "Model could not provide an answer based on the content."
    else:
         progress_status["message"] = "Parsing complete. Answer below."

    # Render the same page, now with the result
    return render_template("parse.html",
                           dom_content=dom_content,
                           parsed_result=parsed_result,
                           parse_description=parse_description, # Show the question again
                           topic=topic,
                           scraped_url=scraped_url)


@app.route("/status", methods=["GET"])
def status():
    """Return the current progress status as JSON."""
    return jsonify(progress_status)

USERNAME = os.getenv("OX_USERNAME")
PASSWORD = os.getenv("OX_PASSWORD")
if __name__ == "__main__":
    # Make sure OX_USERNAME and OX_PASSWORD are set in your .env file
    if not USERNAME or not PASSWORD:
        print("FATAL ERROR: credentials (OX_USERNAME, OX_PASSWORD) not found in environment variables or .env file.")
        exit(1)
    app.run(debug=True) # debug=False for production