from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import time

'''template = (
    "You are tasked with extracting specific information from the following text content: {dom_content}. "
    "Please follow these instructions carefully: \n\n"
    "1. **Extract Information:** Only extract the information that directly matches the provided description: {parse_description}. "
    "2. **No Extra Content:** Do not include any additional text, comments, or explanations in your response. "
    "3. **Empty Response:** If no information matches the description, return an empty string ('')."
    "4. **Direct Data Only:** Your output should contain only the data that is explicitly requested, with no other text."
    "5. **Return in HTML Table if requested**: Format the extracted data as an HTML table without any commnets and newlines when explicitly requested."
    "6. **Table Name**:Give each table an appropriate name."
    "7. **Empty Table if Nothing**: If no data matches, return an empty HTML table."
)'''
template = (
    "**Role:** Web Content Analyst\n"
    "**Input:** {dom_content}\n"
    "**User Query:** {parse_description}\n\n"

    "**Processing Rules:**\n"
    "1. **Content Types Handling**\n"
    "   A. **Factual Data (Prices/Specs/Dates):**\n"
    "      - Extract exact matches only\n"
    "      - Remove duplicates \n"
    "      - Return most prominent value\n"
    "\n"
    "   B. **Subjective Content (Reviews/Opinions):**\n"
    "      - Summarize key sentiments\n"
    "      - Extract notable positive/negative phrases\n"
    "      - Maintain original context\n"
    "\n"
    "2. **Response Protocol**\n"
    "   - For direct requests (What/How):\n"
    "     * Return concise factual answers\n"
    "     * Use bullet points for multiple values\n"
    "\n"
    "   - For analytical requests (Analyze/Review):\n"
    "     * Provide 3-5 sentence summary\n"
    "     * Highlight patterns/consensus\n"
    "     * Don't say your an AI model or give hints that you are an AI model"
    "\n"
    "3. **Formatting Guidelines**\n"
    "   - HTML tables ONLY when explicitly requested\n"
    "   - Natural language for discussion requests\n"
    "   - Empty response ONLY for missing factual data\n"
    "\n"
    "4. **Special Cases**\n"
    "   - Prices: Return current/main price first\n"
    "   - Reviews: Extract 3 key points if available\n"
    "   - Comparisons: Create comparison matrix\n"
    "\n"
    "**Validation Steps:**\n"
    "1. Check if answer directly addresses query\n"
    "2. Verify factual accuracy against source\n"
    "3. Ensure appropriate response length\n"
    "4. Apply requested format strictly\n"
)
#model = ChatGoogleGenerativeAI(model="gemini-2.5-pro-exp-03-25")
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

def parse_with_gemini(dom_chunks, parse_description, update_status=None):
    """Parses all DOM content at once using the Gemini model."""
    # Combine all DOM chunks into a single string.
    full_dom_content = "\n".join(dom_chunks)
    
    if update_status:
        update_status("Preparing content for information exptraction...")

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    try:
        if update_status:
            update_status("Parsing content...")
        start_time = time.time()
        response = chain.invoke({
            "dom_content": full_dom_content,
            "parse_description": parse_description
        })
        end_time = time.time()
        parsing_time = end_time - start_time

        if update_status:
            update_status(f"Parsing completed in {parsing_time:.2f} seconds.")

        # Get the response content as a string
        content = str(response.content if hasattr(response, 'content') else response)
        # Optionally print the content to console for debugging
        print(content)
        # Remove unwanted markdown HTML code block markers
        content = content.replace("```html", "").replace("```", "").strip()
        return content
    except Exception as e:
        if update_status:
            update_status(f"Error processing the content: {e}")
        print(f"Error processing the full DOM content: {e}")
        return ""
