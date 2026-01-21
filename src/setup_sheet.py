from gsheets import ensure_headers_v2

if __name__ == "__main__":
    print("--- Inicializando Estructura V2 de Google Sheets ---")
    
    print("1. Verificando/Creando hoja 'Dashboard_Gastos_v2'...")
    ensure_headers_v2()
    
    print("!Todo listo! Estructura V2 creada.")
