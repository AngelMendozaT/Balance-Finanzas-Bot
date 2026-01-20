from src.gsheets import get_db_connection

def list_sheets():
    client = get_db_connection()
    if not client: return
    ss = client.open_by_key("11LEjhe_ctFTNs5BuWAVecVpzbCAndxoTOBYNMgMXhkA")
    print("Worksheets found:")
    for s in ss.worksheets():
        print(f"- {s.title}")

if __name__ == "__main__":
    list_sheets()
