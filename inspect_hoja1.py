from src.gsheets import get_db_connection

def inspect_data():
    client = get_db_connection()
    ss = client.open_by_key("11LEjhe_ctFTNs5BuWAVecVpzbCAndxoTOBYNMgMXhkA")
    sheet = ss.worksheet("Hoja 1")
    print("Row 1 (Headers):", sheet.row_values(1))
    print("Row 2 (Data):", sheet.row_values(2))

if __name__ == "__main__":
    inspect_data()
