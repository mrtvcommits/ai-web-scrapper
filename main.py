from flask import Flask, render_template, request, jsonify
from scrape import scrape_website, extract_body_content, clean_body_content, split_dom_content
from parse import parse_with_gemini
import time

app = Flask(__name__)

# Global dictionary to store progress status for the current session.
# In a production multi-user environment, you’d use session IDs or another per‑user store.
progress_status = {"message": ""}
def update_progress(message):
        progress_status["message"] = message
        
@app.route("/", methods=["GET"])
def index():
    # Clear progress status on home page load.
    progress_status["message"] = ""
    return render_template("index.html")

@app.route("/scrape", methods=["POST"])
def scrape():
    url = request.form.get("url")
    if not url:
        progress_status["message"] = "Error: No URL provided."
        return "Error: No URL provided.", 400

    progress_status["message"] = "Started scraping website..."

    raw_dom = scrape_website(url, update_status=update_progress)
    body = extract_body_content(raw_dom, update_status=update_progress)
    cleaned = clean_body_content(body, update_status=update_progress)
    
    progress_status["message"] = "Scraping completed."
    # Pass the cleaned content to the next template.
    return render_template("parse.html", dom_content=cleaned, parsed_result=None)

@app.route("/parse", methods=["POST"])
def parse():
    # Retrieve scraped content from the hidden field.
    dom_content = request.form.get("dom_content")
    parse_description = request.form.get("parse_description")

    if not dom_content:
        progress_status["message"] = "Error: Scraped content is missing."
        return "Error: Scraped content is missing.", 400

    if not parse_description:
        progress_status["message"] = "Error: Please provide a description for parsing."
        return "Error: Please provide a description for parsing.", 400

    progress_status["message"] = "Parsing DOM content..."
    # Step 2: Parse the content.
    dom_chunks = split_dom_content(dom_content)
    parsed_result = parse_with_gemini(dom_chunks, parse_description, update_status=update_progress)

    progress_status["message"] = "Parsing completed."
    
    return render_template("parse.html", dom_content=dom_content, parsed_result=parsed_result, parse_description=parse_description)

@app.route("/status", methods=["GET"])
def status():
    """Return the current progress status as JSON."""
    return jsonify(progress_status)

if __name__ == "__main__":
    app.run(debug=True)
