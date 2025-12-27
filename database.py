import mysql.connector
from config import DB_CONFIG

def get_db_connection():
    """Створює та повертає підключення до бази даних."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"Помилка підключення до БД: {err}")
        return None

# Словник відповідності таблиць і колонок
# ВАЖЛИВО: Тут має бути 'hobby'
COLUMN_MAPPING = {
    'profession': 'profession_name',
    'health': 'health_name',
    'hobby': 'hobby_name',
    'phobia': 'phobia_name',
    'luggage': 'luggage_name',
    'fact': 'fact_name'
}

def get_random_from_table(table_name):
    """Витягує ОДИН випадковий елемент з вказаної таблиці."""
    if table_name not in COLUMN_MAPPING:
        print(f"Помилка: Невідома таблиця '{table_name}'")
        return None

    column_name = COLUMN_MAPPING[table_name]
    conn = get_db_connection()
    if conn is None: return None

    cursor = conn.cursor()
    try:
        query = f"SELECT {column_name} FROM {table_name} ORDER BY RAND() LIMIT 1;"
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            return "Дані відсутні"
    except Exception as e:
        print(f"DB Error (Single): {e}")
        return None
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

def get_multiple_random(table_name, count):
    """Витягує КІЛЬКА (count) унікальних випадкових елементів."""
    if table_name not in COLUMN_MAPPING:
        print(f"Помилка: Невідома таблиця '{table_name}'")
        return []

    column_name = COLUMN_MAPPING[table_name]
    conn = get_db_connection()
    if conn is None: return []

    cursor = conn.cursor()
    try:
        query = f"SELECT {column_name} FROM {table_name} ORDER BY RAND() LIMIT {count};"
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Перетворюємо результат [(Res1,), (Res2,)] -> [Res1, Res2]
        return [row[0] for row in results]
        
    except Exception as e:
        print(f"DB Error (Multiple): {e}")
        return []
    finally:
        if cursor: cursor.close()
        if conn: conn.close()