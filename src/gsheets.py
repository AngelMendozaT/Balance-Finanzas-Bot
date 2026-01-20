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

def get_db_connection():
    """
    Connects to Google Sheets using:
    1. Streamlit Secrets (if in Cloud/Deployment)
    2. Local 'credentials.json' (if in Local Development)
    """
    try:
        import streamlit as st
        # Check if running in Streamlit and secrets are available
        # Note: st.secrets works even if not "in streamlit" if .streamlit/secrets.toml exists, 
        # but primarily for Cloud this is key.
        
        # We look for a section [gcp_service_account] in secrets
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            # Create a dict from the secrets object
            # creds_dict = dict(st.secrets["gcp_service_account"]) # Might need specific formatting
            # actually oauth2client expects a dict
            key_dict = dict(st.secrets["gcp_service_account"])
            
            creds = ServiceAccountCredentials.from_json_keyfile_dict(key_dict, SCOPE)
            client = gspread.authorize(creds)
            return client
            
    except ImportError:
        pass # Not using streamlit or not installed
    except Exception as e:
        print(f"Secrets check failed (ignoring if local): {e}")

    # Fallback to local file
    try:
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"Error: {CREDENTIALS_FILE} not found (and no Secrets detected).")
            return None

        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPE)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Error connecting to Google Sheets: {e}")
        return None

def _get_sheet():
    """Helper to get the main worksheet."""
    client = get_db_connection()
    if not client:
        return None
    try:
        # Open by Key (ID) is more robust than name
        try:
            # Try specific name "Hoja 1" first, then default to first sheet
            try:
                sheet = client.open_by_key(SPREADSHEET_ID).worksheet("Hoja 1")
            except:
                sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        except gspread.SpreadsheetNotFound:
            print(f"Spreadsheet ID '{SPREADSHEET_ID}' not found.")
            return None
        return sheet
    except Exception as e:
        print(f"Error opening sheet: {e}")
        return None

def ensure_headers():
    """Checks if headers exist, adds them if not."""
    sheet = _get_sheet()
    if not sheet: 
        return
    
    headers = sheet.row_values(1)
    if not headers or headers != COLUMNS:
        print("Initializing headers...")
        sheet.insert_row(COLUMNS, 1)

def get_transaction_data():
    """
    Fetches all data from the spreadsheet and returns it as a Pandas DataFrame.
    """
    sheet = _get_sheet()
    if not sheet:
        return pd.DataFrame(columns=COLUMNS)

    try:
        data = sheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=COLUMNS)
        
        df = pd.DataFrame(data)
        # Ensure all columns exist even if sheet is empty but has headers
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame(columns=COLUMNS)

def add_transaction(date, amount, description, source, category="Otros", status="pending_classification"):
    """
    Appends a new transaction row with a unique ID.
    """
    sheet = _get_sheet()
    if not sheet:
        return False

    try:
        # Generate ID: Max existing ID + 1
        col_values = sheet.col_values(1) # ID is column 1
        
        # Filter out header 'id' if present and convert rest to ints
        ids = []
        for val in col_values:
            if val.isdigit():
                ids.append(int(val))
        
        new_id = max(ids) + 1 if ids else 1

        row = [new_id, date, amount, description, category, source, status]
        sheet.append_row(row)
        return True
    except Exception as e:
        print(f"Error adding transaction: {e}")
        return False

def update_transaction_category(tx_id, new_category):
    """
    Updates the category and changes status to 'verified' for a given ID.
    """
    sheet = _get_sheet()
    if not sheet:
        return False

    try:
        # Find the row with the given ID
        # Debugging: Print what we are looking for
        print(f"Searching for ID: {tx_id} (Type: {type(tx_id)})")
        
        cell = None
        try:
            # Try finding as string first
            cell = sheet.find(str(tx_id), in_column=1)
        except:
            pass
            
        if not cell:
            # Try finding as integer/exact match? gspread find is string based usually
            # Let's iterate if find fails, which is safer for small datasets
            print("Direct find failed, trying iteration...")
            col_values = sheet.col_values(1)
            for i, val in enumerate(col_values):
                if str(val) == str(tx_id):
                    # gspread rows are 1-indexed. enumerate is 0-indexed. 
                    # Row 1 is header. If col_values[i] matches, row is i+1?
                    # col_values includes header. So index 0 = 'id'.
                    # row number is i + 1
                    from gspread.cell import Cell
                    cell = Cell(row=i+1, col=1, value=val)
                    break
        
        if not cell:
            print(f"Transaction ID {tx_id} not found after search.")
            return False
            
        print(f"Found ID {tx_id} at Row {cell.row}")
        
        # Update Category (Col 5) and Status (Col 7)
        sheet.update_cell(cell.row, 5, new_category)
        sheet.update_cell(cell.row, 7, "verified")
        print(f"Updated Row {cell.row} -> {new_category}, verified")
        return True
    except Exception as e:
        print(f"Error updating transaction: {e}")
        return False

def get_categories():
    """Returns a list of valid categories."""
    return ['Comida', 'Transporte', 'Servicios', 'Ocio', 'Salud', 'Educación', 'Ropa', 'Ahorro', 'Otros']

def create_summary_chart():
    """Creates a basic Pie Chart in a new 'Dashboard' tab."""
    client = get_db_connection()
    if not client: return
    
    try:
        ss = client.open_by_key(SPREADSHEET_ID)
        
        # 1. Ensure Dashboard tab exists
        # 1. Ensure Dashboard tab exists
        try:
            dashboard = ss.worksheet("Dashboard_Gastos_v2")
        except:
            dashboard = ss.add_worksheet(title="Dashboard_Gastos_v2", rows=100, cols=20)
            
        print("Creating chart in 'Dashboard' tab...")
        
        # 1. Clear Sheet to reset layout
        dashboard.clear()

        # 2. Add "Scorecards" at the top
        dashboard.update_acell('C2', "Total Gastado")
        dashboard.update_acell('D2', '=SUM(B6:B)') # Summing the table below

        # 3. Add Aggregation Table starting at row 5
        # Clear the table area to avoid #REF! errors (overwrite protection)
        try:
             dashboard.batch_clear(['A5:B100'])
        except:
             pass

        # Use QUERY for automatic aggregation
        # Reverting to comma syntax as #VALUE! was likely due to empty data or syntax mismatch, trying comma again now that we have data and cleared cells.
        # Actually, let's stick to semicolon if it worked locally? No, standard API usually takes comma.
        # Let's try comma first. if it fails we check locale.
        query_formula = '=QUERY(\'Hoja 1\'!A:G, "SELECT E, SUM(C) WHERE E IS NOT NULL GROUP BY E LABEL E \'Categoría\', SUM(C) \'Total\'", 1)'
        dashboard.update_acell('A5', query_formula)

        # 4. Attempt formatting (Simple bolding via batch_update if possible, or just ignore for now to avoid complexity errors)
        # Let's just set the structure first.
        
        # Basic Pie Chart Spec
        chart_spec = {
            "requests": [
                {
                    "addChart": {
                        "chart": {
                            "spec": {
                                "title": "Gastos por Categoría",
                                "pieChart": {
                                    "legendPosition": "RIGHT_LEGEND",
                                    "domain": {
                                        "sourceRange": {
                                            "sources": [
                                                {
                                                    "sheetId": dashboard.id,
                                                    "startRowIndex": 4, # Row 5 (0-indexed is 4)
                                                    "startColumnIndex": 0,
                                                    "endColumnIndex": 1
                                                }
                                            ]
                                        }
                                    },
                                    "series": {
                                        "sourceRange": {
                                            "sources": [
                                                {
                                                    "sheetId": dashboard.id,
                                                    "startRowIndex": 4,
                                                    "startColumnIndex": 1,
                                                    "endColumnIndex": 2
                                                }
                                            ]
                                        }
                                    }
                                }
                            },
                            "position": {
                                "overlayPosition": {
                                    "anchorCell": {
                                        "sheetId": dashboard.id,
                                        "rowIndex": 4, # Row 5
                                        "columnIndex": 4 # Col E
                                    }
                                }
                            }
                        }
                    }
                }
            ]
        }
        
        ss.batch_update(chart_spec)
        print("Grafico creado exitosamente en la pestana 'Dashboard_Gastos_v2'.")
        return True

    except Exception as e:
        print(f"Error creating chart: {e}")
        traceback.print_exc()
        return False
