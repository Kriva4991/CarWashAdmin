# src/test_license_expiry.py
from database import get_connection
from datetime import datetime, timedelta

conn = get_connection()
cursor = conn.cursor()

print("📅 Тестирование истечения лицензии")
print("=" * 50)
print()
print("Выберите сценарий:")
print("  1. Истекла (30 дней назад)")
print("  2. Остаётся 5 дней")
print("  3. Остаётся 1 день")
print("  4. Сбросить (сегодня)")
print()

choice = input("Введите номер (1-4): ").strip()

if choice == '1':
    # Истекла
    activated_at = (datetime.now() - timedelta(days=35)).isoformat()
    print(f"\n✅ Установлена дата: 35 дней назад")
    
elif choice == '2':
    # 5 дней осталось
    activated_at = (datetime.now() - timedelta(days=25)).isoformat()
    print(f"\n✅ Установлена дата: 25 дней назад (осталось 5 дней)")
    
elif choice == '3':
    # 1 день осталось
    activated_at = (datetime.now() - timedelta(days=29)).isoformat()
    print(f"\n✅ Установлена дата: 29 дней назад (осталось 1 день)")
    
elif choice == '4':
    # Сброс
    activated_at = datetime.now().isoformat()
    print(f"\n✅ Установлена дата: сегодня")
    
else:
    print("❌ Неверный выбор")
    conn.close()
    exit()

# Обновляем в БД
cursor.execute("""
    UPDATE settings SET value = ? WHERE key = 'license_activated_at'
""", (activated_at,))

conn.commit()
conn.close()

print(f"\n📅 Дата активации: {activated_at.split('T')[0]}")
print("🔄 Перезапустите приложение для проверки!")