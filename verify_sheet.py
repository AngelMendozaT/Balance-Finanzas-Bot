from src.gsheets import get_db_connection, SPREADSHEET_ID, WORKSHEET_NAME

def inspect_dashboard():
    client = get_db_connection()
    if not client: return

    try:
        ss = client.open_by_key(SPREADSHEET_ID)
        dash_name = "Dashboard_Gastos_v2"
        
        try:
            ws = ss.worksheet(dash_name)
            print(f"✅ Found Visual Dashboard: '{dash_name}'")
            
            # Check Scorecards
            total_label = ws.acell('C2').value
            total_val = ws.acell('D2').value
            print(f"   [Scorecard] {total_label}: {total_val}")
            
            # Check Table Formula
            table_formula = ws.acell('A5').value
            print(f"   [Query Formula]: {table_formula}")
            
            # Check if query produced results (Cell A6, B6...)
            # A headers are at row like.. wait QUERY puts headers.
            # My query was header=1. So A5 is header ?? No I put query in A5.
            # So A5 is header 'Categoría', B5 is 'Total'.
            # Data starts A6.
            
            headers = ws.get_values("A5:B5")
            print(f"   [Table Headers rendered]: {headers}")
            
            first_row = ws.get_values("A6:B6")
            print(f"   [Table Data Row 1]: {first_row}")
            
        except Exception as e:
            print(f"❌ Error reading dashboard: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_dashboard()
