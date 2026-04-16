# generate_keys.py
from license_manager import LicenseManager

lm = LicenseManager()

print("=" * 50)
print("ГЕНЕРАТОР ЛИЦЕНЗИОННЫХ КЛЮЧЕЙ")
print("=" * 50)
print()

# Бессрочный
lifetime_key = lm.generate_key('lifetime')
print(f"🔑 БЕССРОЧНЫЙ ключ:")
print(f"   {lifetime_key}")
print()

# Пробный
trial_key = lm.generate_key('trial')
print(f"⏳ ПРОБНЫЙ ключ (30 дней):")
print(f"   {trial_key}")
print()

print("Скопируй нужный ключ и отправь пользователю!")