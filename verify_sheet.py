from src.gsheets import get_db_connection, SPREADSHEET_ID, WORKSHEET_NAME

def inspect_data_sheet():
    client = get_db_connection()
    if not client: return

    try:
        ss = client.open_by_key(SPREADSHEET_ID)
        # Check the DATA sheet
        try:
            ws = ss.worksheet(WORKSHEET_NAME) # Gastos_V2_Data
            print(f"✅ Found Data Sheet: '{WORKSHEET_NAME}'")
            
            headers = ws.row_values(1)
            print(f"📋 Headers: {headers}")
            
            rows = ws.get_all_values()
            print(f"📊 Total Rows: {len(rows)}")
            if len(rows) > 1:
                print(f"   First Data Row: {rows[1]}")
            else:
                print("⚠️ DATA SHEET IS EMPTY (Only headers).")

            # Also check source if we need to migrate
            try:
                source_ws = ss.worksheet("Dashboard_Gastos_v2")
                src_rows = source_ws.get_all_values()
                print(f"ℹ️ Potential Source (Dashboard_Gastos_v2) has {len(src_rows)} rows.")
            except:
                print("Source sheet not found.")
                
        except Exception as e:
            print(f"❌ Error reading data sheet: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_data_sheet()
