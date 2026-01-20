from gsheets import ensure_headers, create_summary_chart

if __name__ == "__main__":
    print("--- Inicializando Hoja de Google Sheets ---")
    
    print("1. Verificando cabeceras...")
    ensure_headers()
    
    print("2. Creando gráfico en pestaña Dashboard...")
    create_summary_chart()
    
    print("!Todo listo!")
