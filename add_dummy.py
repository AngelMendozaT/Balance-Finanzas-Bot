from src.gsheets import add_transaction, get_db_connection
from datetime import datetime

def add_dummy():
    print("Adding dummy transaction...")
    success = add_transaction(
        date=datetime.now().strftime("%Y-%m-%d"),
        amount=100.50,
        description="Prueba 1",
        source="Manual",
        category="Comida",
        status="verified"
    )
    if success:
        print("Dummy transaction added.")
    else:
        print("Failed to add dummy transaction.")

if __name__ == "__main__":
    add_dummy()
