import os
import json
import logging
import time
from dotenv import load_dotenv
from models import get_db, Alert

# Load .env so GEMINI_API_KEY is available
load_dotenv()

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

logger = logging.getLogger(__name__)

def run_gemini_analysis(transaction_dict: dict, flagged_rules: list) -> str:
    """
    Calls the Gemini API to analyze a flagged transaction.
    Uses the new google.genai SDK with retry logic for quota limits.
    """
    prompt = (
        f"Analyze this flagged financial transaction: {json.dumps(transaction_dict)}. "
        f"It violated these specific deterministic fraud rules: {json.dumps(flagged_rules)}. "
        f"Please provide a concise one-sentence insight explaining the probable fraud pattern."
    )
    
    if not HAS_GENAI:
        return "[Failsafe] AI Analysis Unavailable: 'google-genai' SDK not installed."
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "[Failsafe] AI Analysis Unavailable: GEMINI_API_KEY environment variable missing."
        
    try:
        client = genai.Client(api_key=api_key)
        
        # Retry up to 3 times with backoff for rate limits
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                return response.text.strip()
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt < 2:
                        wait_time = (attempt + 1) * 10
                        logger.warning(f"Rate limited, retrying in {wait_time}s (attempt {attempt+1}/3)")
                        time.sleep(wait_time)
                    else:
                        return "[Failsafe] Your Gemini API key has exceeded its daily free-tier quota. Please wait for quota reset or use a new key."
                elif "400" in error_msg or "API_KEY_INVALID" in error_msg:
                    return "[Failsafe] Your Gemini API key is invalid. Please check the key in .env file."
                else:
                    raise
        
        return "[Failsafe] AI Analysis failed after 3 retries."
    except Exception as e:
        logger.error(f"Gemini API Error: {str(e)}")
        return f"[Failsafe] AI Error: {str(e)[:120]}"

def process_ai_insight(alert_id: str):
    """
    Background worker function that executes the LLM sequence and securely commits to SQLite.
    Runs asynchronously off the main FastAPI thread to preserve 4GB RAM NFR metrics.
    """
    # Create an independent DB session since this runs outside request lifecycle
    db = next(get_db())
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return
            
        tx = alert.transaction
        tx_dict = {
            "amount": tx.amount,
            "timestamp": tx.timestamp.isoformat() if hasattr(tx.timestamp, 'isoformat') else str(tx.timestamp),
            "merchant": tx.merchant,
            "city": tx.city,
            "category": tx.category
        }
        
        try:
            rules_list = json.loads(alert.flagged_rules)
        except (json.JSONDecodeError, TypeError):
            rules_list = []

        insight = run_gemini_analysis(tx_dict, rules_list)
        alert.ai_insight = insight
        
        if "[Failsafe]" in insight:
            alert.status = "FAILED_AI"
        else:
            alert.status = "ANALYZED"
            
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error in background AI worker: {str(e)}")
    finally:
        db.close()
