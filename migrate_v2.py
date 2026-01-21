from src.gsheets import get_db_connection, SPREADSHEET_ID, WORKSHEET_NAME

def migrate_data():
    print("🚀 Starting Migration...")
    client = get_db_connection()
    if not client: 
        print("❌ No connection.")
        return

    try:
        ss = client.open_by_key(SPREADSHEET_ID)
        
        target_ws = ss.worksheet(WORKSHEET_NAME) # Gastos_V2_Data
        # Try to find the old source.
        # It might be in "Dashboard_Gastos_v2" OR "Hoja 1" (Legacy)
        # Check Hoja 1 first as that was the ORIGINAL original data?
        # No, intermediate step wrote to Dashboard_Gastos_v2.
        
        source_name = "Dashboard_Gastos_v2"
        print(f"📖 Reading from {source_name}...")
        source_ws = ss.worksheet(source_name)
        
        # Read column A to find IDs
        col_a = source_ws.col_values(1)
        print(f"   Found {len(col_a)} rows in column A.")
        
        txns_to_migrate = []
        for i, val in enumerate(col_a):
            if str(val).startswith("txn_"):
                # Get the full row
                # row index is i+1
                row_vals = source_ws.row_values(i+1)
                # Ensure it fits V2 schema (9 cols)
                # If source has 7 cols (old schema), we need to map it.
                # Old: id, date, amount, desc, cat, source, status
                # New: id, date, MONTH, YEAR, amount, desc, cat, source, status
                
                if len(row_vals) >= 7:
                    # Parse date to get month/year
                    date_val = row_vals[1]
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(date_val, '%Y-%m-%d %H:%M:%S')
                        month_str = dt.strftime("%m")
                        year_str = dt.strftime("%Y")
                    except:
                        month_str = "Unknown"
                        year_str = "Unknown"
                        
                    # Construct new row
                    # Old indices: 0=id, 1=date, 2=amount, 3=desc, 4=cat, 5=source, 6=status
                    new_row = [
                        row_vals[0], # id
                        row_vals[1], # date
                        month_str,   # month
                        year_str,    # year
                        row_vals[2], # amount
                        row_vals[3], # desc
                        row_vals[4], # cat
                        row_vals[5], # source
                        row_vals[6]  # status
                    ]
                    txns_to_migrate.append(new_row)

        print(f"🧐 Found {len(txns_to_migrate)} valid transactions.")
        
        if txns_to_migrate:
            print("💾 Writing to new sheet...")
            # Batch append is faster
            target_ws.append_rows(txns_to_migrate)
            print(f"✅ Successfully migrated {len(txns_to_migrate)} rows!")
        else:
            print("⚠️ No transactions found to migrate.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_data()
