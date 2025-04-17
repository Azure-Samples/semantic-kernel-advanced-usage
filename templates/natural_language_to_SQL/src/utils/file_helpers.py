import os
import uuid
import time
from datetime import datetime

def generate_unique_response_filename(query: str = None, prefix: str = "response") -> str:
    """
    Generate a unique filename for storing SQL query responses.
    
    Args:
        query: The user's query (used to create a slugified portion of the filename)
        prefix: Prefix for the filename
        
    Returns:
        A unique filename for the response
    """
    # Create a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a unique identifier
    unique_id = str(uuid.uuid4())[:8]
    
    # Slugify a portion of the query if provided
    query_slug = ""
    if query:
        # Simple slugification: take first few words, replace spaces with underscores
        words = query.lower().replace(',', ' ').replace('.', ' ').split()
        query_slug = "_".join(words[:3])[:30]  # Limit length
        query_slug = "".join(c if c.isalnum() or c == '_' else '' for c in query_slug)
        
        if query_slug:
            query_slug = f"_{query_slug}"
    
    # Create the filename
    filename = f"{prefix}_{timestamp}{query_slug}_{unique_id}.json"
    
    # Ensure the response directory exists
    response_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "responses")
    os.makedirs(response_dir, exist_ok=True)
    
    # Return the full path to the file
    return os.path.join(response_dir, filename)

def clean_old_response_files(max_age_days=7, directory=None):
    """
    Clean up old response files to prevent buildup of unnecessary files.
    
    Args:
        max_age_days: Maximum age of files to keep in days
        directory: Directory containing response files
    """
    if directory is None:
        directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "responses")
    
    if not os.path.exists(directory):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        # Skip if not a file or not a JSON file
        if not os.path.isfile(filepath) or not filename.startswith("response_") or not filename.endswith(".json"):
            continue
            
        # Check file age
        file_age = current_time - os.path.getmtime(filepath)
        if file_age > max_age_seconds:
            try:
                os.remove(filepath)
                print(f"Removed old response file: {filename}")
            except Exception as e:
                print(f"Error removing old file {filename}: {e}")
