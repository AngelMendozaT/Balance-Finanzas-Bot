from gsheets import get_db_connection, SPREADSHEET_NAME

import json

def test_connection():
    print("--- Probando conexión con Google Sheets ---")
    client = get_db_connection()
    
    if client:
        print("✅ Conexión establecida correctamente.")
        
        # Leer el email directamente del archivo credentials.json para evitar errores de atributos
        try:
            with open('credentials.json', 'r') as f:
                creds_data = json.load(f)
                email = creds_data.get('client_email', 'Desconocido')
            print(f"📧 Email del bot: {email}")
            print(f"📋 Asegúrate de compartir tu hoja '{SPREADSHEET_NAME}' con este email.")
        except Exception as e:
            print(f"⚠️ No se pudo leer el email del archivo json: {e}")

        try:
            sheet = client.open(SPREADSHEET_NAME)
            print(f"✅ Se encontró la hoja de cálculo: {sheet.title}")
            print(f"   URL: {sheet.url}")
        except Exception as e:
            # Si es SpreadsheetNotFound (que suele venir en e), damos el mensaje de ayuda
            if "SpreadsheetNotFound" in str(type(e)) or "404" in str(e):
                print(f"❌ No se encontró la hoja '{SPREADSHEET_NAME}'.")
                if 'email' in locals():
                    print(f"👉 SUGERENCIA: Crea una hoja nueva en Google Sheets llamada '{SPREADSHEET_NAME}'")
                    print(f"   y compártela con permisos de EDITOR al email: {email}")
            else:
                print(f"❌ Error al abrir la hoja '{SPREADSHEET_NAME}': {e}")
    else:
        print("❌ No se pudo conectar.")

if __name__ == "__main__":
    test_connection()
