import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import pandas as pd
import json
from datetime import datetime
import traceback

# Scope for Google Sheets and Drive API
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

CREDENTIALS_FILE = "credentials.json"
# Updated to the specific ID provided by the user
SPREADSHEET_ID = "11LEjhe_ctFTNs5BuWAVecVpzbCAndxoTOBYNMgMXhkA"

# Standard columns
COLUMNS = ["id", "date", "amount", "description", "category", "source", "status"]
# V2 Columns with separated date fields for easier pivoting
COLUMNS_V2 = ["id", "date", "month", "year", "amount", "description", "category", "source", "status"]

WORKSHEET_NAME = "Gastos_V2_Data"

def get_db_connection():
    """
    Connects to Google Sheets using:
    1. Streamlit Secrets (if in Cloud/Deployment)
    2. Local 'credentials.json' (if in Local Development)
    3. Environment Variable 'GCP_CREDENTIALS' (Render/Docker)
    """
    try:
        # 1. Streamlit Secrets
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
                key_dict = dict(st.secrets["gcp_service_account"])
                # Fix private key if needed
                if "private_key" in key_dict:
                    key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
                    
                creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, SCOPE)
                client = gspread.authorize(creds)
                return client
        except:
            pass

        # 2. Environment Variable (Render/Railway/Docker)
        # We expect 'GCP_CREDENTIALS' to contain the JSON string
        env_creds = os.environ.get("GCP_CREDENTIALS")
        if env_creds:
            try:
                # If it's a file path
                if os.path.isfile(env_creds):
                    creds = ServiceAccountCredentials.from_json_keyfile_name(env_creds, SCOPE)
                else:
                    # Assume it's a JSON string
                    key_dict = json.loads(env_creds)
                    if "private_key" in key_dict:
                        key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
                    creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, SCOPE)
                
                client = gspread.authorize(creds)
                print("✅ Connected via GCP_CREDENTIALS env var.")
                return client
            except Exception as e:
                print(f"❌ Env var defined but failed: {e}")

        # 3. Fallback to local file
        if os.path.exists(CREDENTIALS_FILE):
            creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
            client = gspread.authorize(creds)
            return client
            
        print(f"❌ Connection failed: {CREDENTIALS_FILE} not found and no Cloud Secrets detected.")
        return None

    except Exception as e:
        print(f"❌ Error connecting to Google Sheets: {e}")
        return None

def _get_sheet(force_v2=True):
    """Helper to get the main worksheet."""
    client = get_db_connection()
    if not client:
        return None
    try:
        # Open by Key (ID) is more robust than name
        sh = client.open_by_key(SPREADSHEET_ID)
        
        target_name = WORKSHEET_NAME if force_v2 else "Hoja 1"
        try:
            sheet = sh.worksheet(target_name)
        except gspread.WorksheetNotFound:
            if force_v2:
                print(f"Worksheet '{target_name}' not found. Creating it...")
                sheet = sh.add_worksheet(title=target_name, rows=1000, cols=20)
            else:
                # Fallback to sheet1 if looking for legacy and specific name fails
                sheet = sh.sheet1
                
        return sheet
    except Exception as e:
        print(f"Error opening sheet: {e}")
        return None

def ensure_headers_v2():
    """Checks if headers exist in V2 sheet, adds them if not."""
    sheet = _get_sheet(force_v2=True)
    if not sheet:
        return

    try:
        # Get first row
        headers = sheet.row_values(1)
        if not headers:
            print("V2 Sheet is empty. Adding headers...")
            sheet.append_row(COLUMNS_V2)
        else:
             # Check if headers match V2
            if headers != COLUMNS_V2:
                print(f"Warning: Headers in {WORKSHEET_NAME} mismatch. Expected {COLUMNS_V2}, got {headers}")
                # Ideally we might migrate or warn, for now just print
    except Exception as e:
        print(f"Error checking headers: {e}")
    sheet = _get_sheet()
    if not sheet: 
        return
    
    headers = sheet.row_values(1)
    if not headers or headers != COLUMNS:
        print("Initializing headers...")
        sheet.insert_row(COLUMNS, 1)

def get_transactions_df():
    """Fetch all transactions as a Pandas DataFrame."""
    sheet = _get_sheet(force_v2=True)
    if not sheet:
        return pd.DataFrame(columns=COLUMNS_V2)

    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        
        # Ensure V2 columns if empty or missing
        if df.empty:
            return pd.DataFrame(columns=COLUMNS_V2)
            
        return df
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return pd.DataFrame(columns=COLUMNS_V2)

def add_transaction(date, amount, description, source, category='Otros', status='pending_classification'):
    """Add a new transaction to the Google Sheet."""
    sheet = _get_sheet(force_v2=True)
    if not sheet:
        return False

    try:
        # Generate ID (Timestamp based)
        import time
        txn_id = f"txn_{int(time.time()*1000)}"
        
        # Calculate Month and Year
        # Input date format expected: YYYY-MM-DD HH:MM:SS
        try:
            dt_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            # Making it simple: MM format for easy sorting
            month_str = dt_obj.strftime("%m")
            year_str = dt_obj.strftime("%Y")
        except:
            month_str = "Unknown"
            year_str = "Unknown"

        # Row Data matching COLUMNS_V2
        # ["id", "date", "month", "year", "amount", "description", "category", "source", "status"]
        row = [txn_id, date, month_str, year_str, amount, description, category, source, status]
        
        sheet.append_row(row)
        print("Transaction added successfully.")
        return True
    except Exception as e:
        print(f"Error adding transaction: {e}")
        traceback.print_exc()
        return False

def update_category(txn_id, category, status="verified"):
    """Update category and status for a transaction."""
    sheet = _get_sheet(force_v2=True)
    if not sheet:
        return False
        
    try:
        # Find cell with txn_id
        # In V2 we use string IDs like txn_123456789, so straight find should work better
        cell = sheet.find(str(txn_id), in_column=1)
        
        if not cell:
            print(f"Transaction {txn_id} not found.")
            return False
            
        # Update Category (Column G -> 7 in V2)
        # COLUMNS_V2 = ["id", "date", "month", "year", "amount", "description", "category", "source", "status"]
        
        sheet.update_cell(cell.row, 7, category)
        sheet.update_cell(cell.row, 9, status)
        
        print(f"Updated {txn_id}: {category} ({status})")
        return True
    except Exception as e:
        print(f"Error updating category: {e}")
        return False

def get_categories():
    """Returns a list of valid categories."""
    return ['Comida', 'Transporte', 'Servicios', 'Ocio', 'Salud', 'Educación', 'Ropa', 'Ahorro', 'Otros']

def create_summary_chart():
    """Creates a visually appealing summary in 'Dashboard_Gastos_v2' linked to 'Gastos_V2_Data'."""
    client = get_db_connection()
    if not client: return False
    
    try:
        ss = client.open_by_key(SPREADSHEET_ID)
        
        # 1. Ensure Dashboard tab exists (Visual Only)
        dash_name = "Dashboard_Gastos_v2"
        try:
            dashboard = ss.worksheet(dash_name)
        except:
            dashboard = ss.add_worksheet(title=dash_name, rows=100, cols=20)
            
        print(f"Update visual dashboard: {dash_name}")
        
        # 2. Clear Sheet to reset layout
        dashboard.clear()

        # 3. Add "Scorecards" at the top
        dashboard.update_acell('C2', "Total Gastado V2")
        dashboard.update_acell('D2', '=SUM(B6:B)') 

        # 4. Add Aggregation Table starting at row 5
        try:
             dashboard.batch_clear(['A5:B100'])
        except:
             pass

        # Query referencing Gastos_V2_Data
        # Columns in V2: 
        # A=id, B=date, C=month, D=year, E=amount, F=description, G=category, H=source, I=status
        # We want Group By Category (G), Sum Amount (E).
        # Labels: G 'Categoría', Sum(E) 'Total'
        query_formula = f'=QUERY(\'{WORKSHEET_NAME}\'!A:I, "SELECT G, SUM(E) WHERE G IS NOT NULL GROUP BY G LABEL G \'Categoría\', SUM(E) \'Total\'", 1)'
        dashboard.update_acell('A5', query_formula)

        # 5. Chart creation (Simplified, passing for now to avoid complexity, Google Sheets needs strict JSON)
        # We will just leave the table + scorecards which is safer and "looks good" enough for auto-setup.
        # User can add fancy charts manually on top of this aggregation.
        
        print(f"Dashboard {dash_name} updated.")
        return True

    except Exception as e:
        print(f"Error creating chart: {e}")
        import traceback
        traceback.print_exc()
        return False
