from src.db import add_transaction
from datetime import datetime

if __name__ == "__main__":
    print("🚀 Intentando insertar gasto de prueba...")
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # add_transaction(date, amount, description, source, category, status)
        success = add_transaction(
            now, 
            10.00, 
            'Prueba de Conección V2', 
            'Script', 
            'Comida', 
            'verified'
        )
        
        if success:
            print("✅ Gasto de prueba agregado EXITOSAMENTE.")
        else:
            print("❌ Falló la inserción.")
            
    except Exception as e:
        print(f"❌ Error crítico: {e}")
