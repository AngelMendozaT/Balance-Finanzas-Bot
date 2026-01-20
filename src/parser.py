import re
import json
from datetime import datetime

def parse_mock_email(subject, body):
    """
    Simulates parsing an email content using Regex/Heuristics.
    In the future, this will be replaced/augmented by LLM calls.
    """
    data = {
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "amount": 0.0,
        "description": "Unknown",
        "source": "Unknown",
        "category": "Otros",
        "status": "pending_classification"
    }

    # Detect Source
    if "Yape" in subject or "Yape" in body:
        data["source"] = "Yape"
    elif "BCP" in subject or "BCP" in body:
        data["source"] = "BCP"
    
    # Extract Amount (Regex for S/ XX.XX)
    amount_match = re.search(r'S/\s?(\d+\.?\d*)', body)
    if amount_match:
        data["amount"] = float(amount_match.group(1))

    # Heuristic Classification for BCP (Mock)
    if data["source"] == "BCP":
        if "Uber" in body:
            data["description"] = "Uber Trip"
            data["category"] = "Transporte"
            data["status"] = "verified"
        elif "Netflix" in body:
            data["description"] = "Netflix Subscription"
            data["category"] = "Ocio"
            data["status"] = "verified"
    
    # Yape Logic (Always uncertain unless specific)
    if data["source"] == "Yape":
        data["description"] = "Yape sent/received"
        data["status"] = "pending_classification" # Needs user/bot input

    return data

if __name__ == "__main__":
    # Test
    sample_body = "Hola, enviaste un Yape de S/ 20.00 a Juan."
    print(parse_mock_email("Confirmacion Yape", sample_body))
