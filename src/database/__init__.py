# src/database/__init__.py
import sqlite3
import os

# Определяем путь к базе данных
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'data', 'carwash.db')

def get_connection():
    """Возвращает соединение с БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создаёт таблицы, если их нет"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Таблица услуг
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            duration_min INTEGER DEFAULT 60
        )
    """)
    
    # Таблица заказов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            car_number TEXT NOT NULL,
            car_model TEXT,
            client_phone TEXT,
            client_id INTEGER,
            car_class_id INTEGER,
            status TEXT DEFAULT 'queue',
            total_price REAL,
            payment_method TEXT,
            comment TEXT,
            shift_id INTEGER
        )
    """)
    
    # Таблица элементов заказа
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            service_id INTEGER,
            base_price REAL,
            final_price REAL,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (service_id) REFERENCES services(id)
        )
    """)
    
    # Таблица клиентов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            car_number TEXT,
            car_model TEXT,
            phone TEXT,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица настроек
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    
    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            is_active INTEGER DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица смен
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            revenue REAL DEFAULT 0
        )
    """)
    
    # Таблица классов авто
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS car_classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            coefficient REAL DEFAULT 1.0
        )
    """)
    
    # Пользователь по умолчанию
    cursor.execute("SELECT count(*) FROM users")
    if cursor.fetchone()[0] == 0:
        import bcrypt
        default_password = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        cursor.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        """, ("admin", default_password.decode(), "admin"))
        print("✅ Пользователь по умолчанию создан: admin / admin123")
    
    # Классы авто по умолчанию
    cursor.execute("SELECT count(*) FROM car_classes")
    if cursor.fetchone()[0] == 0:
        car_classes = [
            ('Мото / Квадро', 0.5),
            ('Малый класс (A, B)', 1.0),
            ('Средний класс (C, D)', 1.2),
            ('Бизнес класс (E, F)', 1.5),
            ('Внедорожник / Джип', 1.7),
            ('Минивэн / Фургон', 1.8),
            ('Грузовой / Микроавтобус', 2.0)
        ]
        cursor.executemany(
            "INSERT INTO car_classes (name, coefficient) VALUES (?, ?)",
            car_classes
        )
        print("✅ Классы автомобилей добавлены.")
    
    # Услуги по умолчанию
    cursor.execute("SELECT count(*) FROM services")
    if cursor.fetchone()[0] == 0:
        services = [
            ('Мойка кузова', 500.0, 30),
            ('Мойка салона', 1500.0, 60),
            ('Комплексная мойка автомобиля', 2500.0, 90),
            ('Только коврики', 200.0, 10),
            ('Антидождь', 1500.0, 45),
            ('Чернение резины', 500.0, 20),
            ('Покрытие воском', 2000.0, 60),
            ('Покрытие кварцом', 5000.0, 120)
        ]
        cursor.executemany(
            "INSERT INTO services (name, price, duration_min) VALUES (?, ?, ?)",
            services
        )
        print("✅ Базовые услуги добавлены.")

        # Таблица расходных материалов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consumables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            unit TEXT DEFAULT 'шт',
            current_stock REAL DEFAULT 0,
            min_stock REAL DEFAULT 0,
            cost_per_unit REAL DEFAULT 0,
            last_restock DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица списания расходников
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consumable_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consumable_id INTEGER NOT NULL,
            order_id INTEGER,
            quantity REAL NOT NULL,
            used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (consumable_id) REFERENCES consumables(id),
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)
    
    # Базовые расходники (если таблица пуста)
    cursor.execute("SELECT count(*) FROM consumables")
    if cursor.fetchone()[0] == 0:
        default_consumables = [
            ('Шампунь для бесконтактной мойки', 'литр', 50, 10, 500),
            ('Шампунь для ручной мойки', 'литр', 30, 5, 600),
            ('Воск жидкий', 'литр', 20, 5, 800),
            ('Антидождь', 'литр', 10, 2, 1500),
            ('Чернитель резины', 'литр', 15, 3, 400),
            ('Очиститель дисков', 'литр', 25, 5, 350),
            ('Салфетки микрофибра', 'шт', 100, 20, 50),
            ('Губки', 'шт', 50, 10, 30),
        ]
        cursor.executemany("""
            INSERT INTO consumables (name, unit, current_stock, min_stock, cost_per_unit)
            VALUES (?, ?, ?, ?, ?)
        """, default_consumables)
        print("✅ Базовые расходники добавлены.")

    cursor.execute("""
        INSERT OR IGNORE INTO settings (key, value)
        VALUES ('language', 'ru')
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ База данных готова: {DB_PATH}")

def create_indexes():
    """Создаёт индексы для оптимизации"""
    conn = get_connection()
    cursor = conn.cursor()
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_orders_car_number ON orders(car_number)",
        "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
        "CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_orders_client_id ON orders(client_id)",
        "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_clients_car_number ON clients(car_number)",
        "CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone)",
    ]
    
    created = 0
    for sql in indexes:
        try:
            cursor.execute(sql)
            created += 1
        except Exception as e:
            print(f"⚠️ Индекс не создан: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ Создано индексов: {created}")

if __name__ == "__main__":
    init_db()
    create_indexes()