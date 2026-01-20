from src.gsheets import get_db_connection

def verify_dashboard():
    client = get_db_connection()
    if not client: return
    ss = client.open_by_key("11LEjhe_ctFTNs5BuWAVecVpzbCAndxoTOBYNMgMXhkA")
    try:
        sheet = ss.worksheet("Dashboard_Gastos_v2")
        print(f"Sheet '{sheet.title}' found.")
        print("Values in A1:B5:")
        print(sheet.get('A1:B5'))
    except Exception as e:
        print(f"Error accessing dashboard: {e}")

if __name__ == "__main__":
    verify_dashboard()
