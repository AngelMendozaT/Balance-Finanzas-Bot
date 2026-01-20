from src.gsheets import get_db_connection

def test_update():
    client = get_db_connection()
    if not client: return
    ss = client.open_by_key("11LEjhe_ctFTNs5BuWAVecVpzbCAndxoTOBYNMgMXhkA")
    dashboard = ss.worksheet("Dashboard_Gastos_v2")
    
    print("Testing simple update...")
    try:
        dashboard.update_acell('A10', "Test")
        print("Simple update successful")
    except Exception as e:
        print(f"Simple update failed: {e}")

    print("Testing formula update...")
    try:
        formula = '=QUERY(Sheet1!A:G, "SELECT E, SUM(C) WHERE E IS NOT NULL GROUP BY E LABEL E \'Categoria\', SUM(C) \'Total\'", 1)'
        dashboard.update_acell('A1', formula)
        print("Formula update successful")
    except Exception as e:
        print(f"Formula update failed: {e}")

if __name__ == "__main__":
    test_update()
