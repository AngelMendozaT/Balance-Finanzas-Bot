import gsheets
from datetime import datetime

def init_db():
    """Checks and creates headers in the Google Sheet."""
    gsheets.ensure_headers()
    print("Google Sheets initialized with headers.")

def add_transaction(date, amount, description, source, category='Otros', status='pending_classification'):
    """Add a new transaction via Google Sheets."""
    print(f"Adding transaction: {description}, {amount}")
    return gsheets.add_transaction(date, amount, description, source, category, status)

def get_transactions_df():
    """Return all transactions from Google Sheets as DataFrame."""
    return gsheets.get_transaction_data()

def update_transaction_category(tx_id, new_category):
    """Update the category of a specific transaction in Sheets."""
    return gsheets.update_transaction_category(tx_id, new_category)

def get_categories():
    """Get list of categories."""
    return gsheets.get_categories()

if __name__ == "__main__":
    init_db()
    
    # Test adding a dummy transaction
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    add_transaction(now, 50.00, 'Test Manual Integration', 'Terminal', 'Otros', 'pending_classification')
    
    print("Test transaction added. Checking data...")
    df = get_transactions_df()
    print(df.head())

