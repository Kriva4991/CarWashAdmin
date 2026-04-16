# src/database/migrations.py
"""
Миграции для системы ролей и прав доступа
"""

from database import get_connection


def migrate_roles_and_permissions():
    """Добавляет таблицы для ролей, прав и аудита"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Обновляем таблицу users (добавляем role если нет)
    cursor.execute("PRAGMA table_info(users)")
    columns = [col['name'] for col in cursor.fetchall()]
    
    if 'role' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'admin'")
        print("✅ Добавлена колонка role в users")
    
    if 'is_active' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
        print("✅ Добавлена колонка is_active в users")
    
    if 'last_login' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
        print("✅ Добавлена колонка last_login в users")
    
    # 2. Таблица прав доступа
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            category TEXT
        )
    """)
    
    # 3. Таблица связи ролей и прав
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS role_permissions (
            role TEXT NOT NULL,
            permission_id INTEGER NOT NULL,
            PRIMARY KEY (role, permission_id),
            FOREIGN KEY (permission_id) REFERENCES permissions(id)
        )
    """)
    
    # 4. Таблица аудита (журнал действий)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    
    # 5. Заполняем права по умолчанию
    default_permissions = [
        # Заказы
        ('view_orders', 'Просмотр заказов', 'orders'),
        ('create_order', 'Создание заказа', 'orders'),
        ('edit_order', 'Редактирование заказа', 'orders'),
        ('delete_order', 'Удаление заказа', 'orders'),
        ('change_order_status', 'Изменение статуса заказа', 'orders'),
        
        # Клиенты
        ('view_clients', 'Просмотр клиентов', 'clients'),
        ('edit_client', 'Редактирование клиента', 'clients'),
        ('export_clients', 'Экспорт клиентов', 'clients'),
        
        # Услуги
        ('view_services', 'Просмотр услуг', 'services'),
        ('manage_services', 'Управление услугами', 'services'),
        
        # Отчёты
        ('view_reports', 'Просмотр отчётов', 'reports'),
        ('export_reports', 'Экспорт отчётов', 'reports'),
        
        # Настройки
        ('view_settings', 'Просмотр настроек', 'settings'),
        ('edit_settings', 'Изменение настроек', 'settings'),
        ('manage_users', 'Управление пользователями', 'settings'),
        
        # Смены
        ('view_shifts', 'Просмотр смен', 'shifts'),
        ('manage_shifts', 'Управление сменами', 'shifts'),
        
        # Расходники
        ('view_consumables', 'Просмотр расходников', 'consumables'),
        ('manage_consumables', 'Управление расходниками', 'consumables'),
    ]
    
    for perm in default_permissions:
        cursor.execute("""
            INSERT OR IGNORE INTO permissions (name, description, category)
            VALUES (?, ?, ?)
        """, perm)
    
    # 6. Назначаем права ролям
    cursor.execute("SELECT id, name FROM permissions")
    all_perms = {row['name']: row['id'] for row in cursor.fetchall()}
    
    # Админ — все права
    for perm_id in all_perms.values():
        cursor.execute("""
            INSERT OR IGNORE INTO role_permissions (role, permission_id)
            VALUES ('admin', ?)
        """, (perm_id,))
    
    # Менеджер — ограниченные права
    manager_perms = [
        'view_orders', 'create_order', 'edit_order', 'change_order_status',
        'view_clients', 'edit_client', 'export_clients',
        'view_services',
        'view_reports', 'export_reports',
        'view_shifts', 'manage_shifts',
        'view_consumables',
    ]
    
    for perm_name in manager_perms:
        if perm_name in all_perms:
            cursor.execute("""
                INSERT OR IGNORE INTO role_permissions (role, permission_id)
                VALUES ('manager', ?)
            """, (all_perms[perm_name],))
    
    # Мойщик — минимальные права
    washer_perms = [
        'view_orders', 'change_order_status',
        'view_clients',
    ]
    
    for perm_name in washer_perms:
        if perm_name in all_perms:
            cursor.execute("""
                INSERT OR IGNORE INTO role_permissions (role, permission_id)
                VALUES ('washer', ?)
            """, (all_perms[perm_name],))
    
    conn.commit()
    conn.close()
    print("✅ Миграция ролей и прав завершена")


if __name__ == "__main__":
    migrate_roles_and_permissions()