from src.gsheets import get_db_connection

def check_ids():
    client = get_db_connection()
    if not client: return
    ss = client.open_by_key("11LEjhe_ctFTNs5BuWAVecVpzbCAndxoTOBYNMgMXhkA")
    print(f"Spreadsheet: {ss.title}")
    print("-" * 30)
    for s in ss.worksheets():
        print(f"Name: {s.title} | ID: {s.id}")

    # Also check content of Dashboard_Gastos_v2 to be sure
    try:
        dash = ss.worksheet("Dashboard_Gastos_v2")
        print("-" * 30)
        print(f"Content of 'Dashboard_Gastos_v2' (A1:E5):")
        print(dash.get('A1:E5'))
    except:
        print("Could not read Dashboard_Gastos_v2")

if __name__ == "__main__":
    check_ids()
