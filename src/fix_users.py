# fix_users.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import bcrypt
from database import get_connection

def fix_users():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Удаляем тестовых пользователей (кроме admin)
    cursor.execute("DELETE FROM users WHERE username != 'admin'")
    
    # Проверяем admin
    cursor.execute("SELECT password_hash FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    
    if admin:
        # Проверяем, валидный ли хеш у admin
        try:
            password_hash = admin['password_hash']
            if isinstance(password_hash, str):
                password_hash = password_hash.encode('utf-8')
            bcrypt.checkpw(b"admin123", password_hash)
            print("✅ Хеш admin валидный")
        except:
            # Пересоздаём admin
            print("⚠️ Хеш admin невалидный, пересоздаём...")
            password_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt())
            cursor.execute("""
                UPDATE users SET password_hash = ? WHERE username = 'admin'
            """, (password_hash.decode(),))
            print("✅ Admin обновлён")
    
    # Создаём тестовых пользователей с ПРАВИЛЬНЫМ хешем
    users = [
        ('test', 'test123', 'washer'),
        ('manager', 'manager123', 'manager'),
    ]
    
    for username, password, role in users:
        # Важно: хеш должен быть строкой!
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cursor.execute("""
            INSERT INTO users (username, password_hash, role, is_active)
            VALUES (?, ?, ?, 1)
        """, (username, password_hash.decode('utf-8'), role))
        print(f"✅ Создан пользователь: {username} / {password} (роль: {role})")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Все пользователи исправлены!")
    print("   admin / admin123")
    print("   test / test123")
    print("   manager / manager123")

if __name__ == "__main__":
    fix_users()