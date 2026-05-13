import sqlite3
import os

def clear_sqlite_db():
    # Nombre del archivo que se ve en tu imagen image_49bef8.png
    db_file = "body_analytics.db"
    
    if not os.path.exists(db_file):
        print(f"❌ No se encontró el archivo {db_file} en esta carpeta.")
        return

    try:
        # Conexión a la base de datos local
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # 1. Borramos los datos de la tabla de pesos
        cursor.execute("DELETE FROM weight_entries")
        
        # 2. Opcional: Reiniciar el contador de IDs (el autoincrement)
        # Esto hace que el siguiente registro vuelva a ser el ID 1
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='weight_entries'")
        
        conn.commit()
        print(f"✅ Tabla 'weight_entries' vaciada con éxito en {db_file}")
        
    except sqlite3.Error as e:
        print(f"❌ Error de SQLite: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    confirm = input("⚠️ ¿Confirmas borrar todos los registros LOCALES? (s/n): ")
    if confirm.lower() == 's':
        clear_sqlite_db()
    else:
        print("Operación cancelada.")