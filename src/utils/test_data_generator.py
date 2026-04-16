# src/utils/test_data_generator.py
"""
Генератор тестовых данных для демонстрации и тестирования
"""

import random
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection


class TestDataGenerator:
    """Генератор тестовых данных"""
    
    # Данные для генерации
    CAR_BRANDS = [
        "Toyota", "Honda", "BMW", "Mercedes", "Audi", "Lexus", "Kia", "Hyundai",
        "Volkswagen", "Skoda", "Renault", "Nissan", "Mazda", "Mitsubishi", "Lada",
        "Ford", "Chevrolet", "Opel", "Peugeot", "Citroen"
    ]
    
    CAR_MODELS = {
        "Toyota": ["Camry", "Corolla", "RAV4", "Land Cruiser", "Highlander"],
        "Honda": ["Civic", "Accord", "CR-V", "Pilot", "Fit"],
        "BMW": ["X5", "X3", "530i", "320i", "X6", "M3", "M5"],
        "Mercedes": ["E200", "S500", "GLE", "GLC", "C180", "AMG GT"],
        "Audi": ["A4", "A6", "Q5", "Q7", "A8", "Q8", "e-tron"],
        "Lexus": ["RX350", "LX570", "ES250", "NX200", "GX460"],
        "Kia": ["Rio", "Sportage", "Sorento", "Cerato", "Optima", "K5"],
        "Hyundai": ["Solaris", "Creta", "Tucson", "Santa Fe", "Elantra", "Sonata"],
        "Volkswagen": ["Polo", "Golf", "Tiguan", "Passat", "Touareg"],
        "Skoda": ["Octavia", "Rapid", "Kodiaq", "Superb", "Karoq"],
        "Renault": ["Logan", "Sandero", "Duster", "Kaptur", "Arkana"],
        "Nissan": ["Qashqai", "X-Trail", "Juke", "Murano", "Almera"],
        "Mazda": ["CX-5", "Mazda 6", "Mazda 3", "CX-9", "CX-30"],
        "Mitsubishi": ["Outlander", "L200", "Pajero Sport", "ASX", "Eclipse Cross"],
        "Lada": ["Granta", "Vesta", "Niva", "Largus", "XRAY", "Priora"],
        "Ford": ["Focus", "Kuga", "Mondeo", "Explorer", "Fiesta"],
        "Chevrolet": ["Cruze", "Aveo", "Traverse", "Tahoe", "Camaro"],
        "Opel": ["Astra", "Corsa", "Insignia", "Mokka", "Grandland"],
        "Peugeot": ["308", "3008", "408", "508", "2008"],
        "Citroen": ["C4", "C3", "C5 Aircross", "Berlingo", "Jumper"]
    }
    
    CAR_LETTERS = ["А", "В", "Е", "К", "М", "Н", "О", "Р", "С", "Т", "У", "Х"]
    
    FIRST_NAMES = ["Александр", "Михаил", "Иван", "Дмитрий", "Андрей", "Сергей", "Алексей", 
                   "Максим", "Владимир", "Николай", "Игорь", "Павел", "Роман", "Виктор"]
    
    STREETS = ["Ленина", "Мира", "Пушкина", "Гагарина", "Советская", "Молодёжная", 
               "Центральная", "Школьная", "Садовая", "Лесная", "Октябрьская", "Победы"]
    
    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
    
    def generate_car_number(self) -> str:
        """Генерирует случайный госномер"""
        letter1 = random.choice(self.CAR_LETTERS)
        number = str(random.randint(100, 999))
        letter2 = random.choice(self.CAR_LETTERS)
        letter3 = random.choice(self.CAR_LETTERS)
        region = str(random.randint(1, 199))
        return f"{letter1}{number}{letter2}{letter3}{region}"
    
    def generate_phone(self) -> str:
        """Генерирует случайный телефон"""
        return f"+7{random.randint(900, 999)}{random.randint(1000000, 9999999)}"
    
    def generate_car_info(self) -> tuple:
        """Генерирует информацию об авто (марка, модель)"""
        brand = random.choice(self.CAR_BRANDS)
        model = random.choice(self.CAR_MODELS.get(brand, ["Base"]))
        return brand, f"{brand} {model}"
    
    def generate_clients(self, count: int = 30) -> List[int]:
        """
        Генерирует тестовых клиентов
        
        Returns:
            Список ID созданных клиентов
        """
        print(f"👤 Генерация {count} клиентов...")
        client_ids = []
        
        # Очищаем существующих клиентов (опционально)
        # self.cursor.execute("DELETE FROM clients")
        
        for i in range(count):
            car_number = self.generate_car_number()
            brand, car_model = self.generate_car_info()
            phone = self.generate_phone() if random.random() > 0.3 else None
            comment = random.choice([
                "VIP клиент", "Любит кофе", "Торопится всегда", 
                "Постоянный", "", "", "", "Скидка 10%", None, None
            ]) if random.random() > 0.5 else None
            
            self.cursor.execute("""
                INSERT INTO clients (car_number, car_model, phone, comment, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                car_number,
                car_model,
                phone,
                comment,
                datetime.now() - timedelta(days=random.randint(1, 365))
            ))
            
            client_ids.append(self.cursor.lastrowid)
        
        self.conn.commit()
        print(f"   ✅ Создано {count} клиентов")
        return client_ids
    
    def generate_orders(self, client_ids: List[int], count: int = 100) -> List[int]:
        """
        Генерирует тестовые заказы
        
        Args:
            client_ids: Список ID клиентов
            count: Количество заказов
            
        Returns:
            Список ID созданных заказов
        """
        print(f"📋 Генерация {count} заказов...")
        
        # Получаем список услуг
        self.cursor.execute("SELECT id, name, price FROM services")
        services = self.cursor.fetchall()
        
        if not services:
            print("   ⚠️ Нет услуг в базе! Сначала добавьте услуги.")
            return []
        
        # Получаем классы авто
        self.cursor.execute("SELECT id FROM car_classes")
        car_classes = [row['id'] for row in self.cursor.fetchall()]
        if not car_classes:
            car_classes = [2]  # Средний класс по умолчанию
        
        order_ids = []
        statuses = ['queue', 'process', 'done', 'done', 'done']  # done чаще
        payment_methods = ['cash', 'card', 'transfer', 'sbp']
        
        for i in range(count):
            # Выбираем случайного клиента или создаём без клиента
            client_id = random.choice(client_ids) if client_ids and random.random() > 0.2 else None
            
            if client_id:
                # Получаем данные клиента
                self.cursor.execute(
                    "SELECT car_number, car_model, phone FROM clients WHERE id = ?",
                    (client_id,)
                )
                client = self.cursor.fetchone()
                car_number = client['car_number']
                car_model = client['car_model']
                phone = client['phone']
            else:
                car_number = self.generate_car_number()
                brand, car_model = self.generate_car_info()
                phone = self.generate_phone() if random.random() > 0.3 else None
            
            # Выбираем случайные услуги (1-4)
            num_services = random.randint(1, min(4, len(services)))
            selected_services = random.sample(services, num_services)
            
            total_price = 0
            order_items = []
            
            for service in selected_services:
                quantity = random.randint(1, 2)
                price = service['price']
                # Иногда даём скидку
                if random.random() < 0.15:
                    price = price * random.uniform(0.7, 0.95)
                
                total_price += price * quantity
                order_items.append({
                    'service_id': service['id'],
                    'quantity': quantity,
                    'base_price': service['price'],
                    'final_price': price
                })
            
            # Случайная дата в пределах последних 90 дней
            days_ago = random.randint(0, 90)
            order_date = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 12))
            
            status = random.choice(statuses)
            payment_method = random.choice(payment_methods)
            
            # Создаём заказ
            self.cursor.execute("""
                INSERT INTO orders (
                    car_number, car_model, client_phone, client_id,
                    car_class_id, status, total_price, payment_method,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                car_number,
                car_model,
                phone,
                client_id,
                random.choice(car_classes),
                status,
                total_price,
                payment_method,
                order_date,
                order_date
            ))
            
            order_id = self.cursor.lastrowid
            order_ids.append(order_id)
            
            # Добавляем услуги
            for item in order_items:
                self.cursor.execute("""
                    INSERT INTO order_items (order_id, service_id, quantity, base_price, final_price)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    order_id,
                    item['service_id'],
                    item['quantity'],
                    item['base_price'],
                    item['final_price']
                ))
        
        self.conn.commit()
        print(f"   ✅ Создано {count} заказов")
        return order_ids
    
    def generate_consumable_usage(self, order_ids: List[int]):
        """Генерирует списания расходников для заказов"""
        print("🧴 Генерация списаний расходников...")
        
        # Получаем расходники
        self.cursor.execute("SELECT id, name, unit FROM consumables")
        consumables = self.cursor.fetchall()
        
        if not consumables:
            print("   ⚠️ Нет расходников в базе!")
            return
        
        usage_count = 0
        for order_id in order_ids[:len(order_ids)//2]:  # Для половины заказов
            # Выбираем 1-3 случайных расходника
            for _ in range(random.randint(1, 3)):
                consumable = random.choice(consumables)
                quantity = round(random.uniform(0.1, 2.0), 1)
                
                # Списываем
                self.cursor.execute("""
                    UPDATE consumables 
                    SET current_stock = MAX(0, current_stock - ?),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND current_stock >= ?
                """, (quantity, consumable['id'], quantity))
                
                if self.cursor.rowcount > 0:
                    # Записываем использование
                    self.cursor.execute("""
                        INSERT INTO consumable_usage (consumable_id, order_id, quantity, notes)
                        VALUES (?, ?, ?, ?)
                    """, (consumable['id'], order_id, quantity, f"Списание по заказу #{order_id}"))
                    usage_count += 1
        
        self.conn.commit()
        print(f"   ✅ Создано {usage_count} списаний расходников")
    
    def generate_all(self, clients: int = 30, orders: int = 100):
        """
        Генерирует все тестовые данные
        
        Args:
            clients: Количество клиентов
            orders: Количество заказов
        """
        print("\n" + "="*50)
        print("🚀 ГЕНЕРАЦИЯ ТЕСТОВЫХ ДАННЫХ")
        print("="*50)
        
        # Генерируем клиентов
        client_ids = self.generate_clients(clients)
        
        # Генерируем заказы
        order_ids = self.generate_orders(client_ids, orders)
        
        # Генерируем списания расходников
        if order_ids:
            self.generate_consumable_usage(order_ids)
        
        print("\n" + "="*50)
        print("✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА!")
        print("="*50)
        print(f"   👤 Клиентов: {clients}")
        print(f"   📋 Заказов: {orders}")
        print("="*50 + "\n")
    
    def close(self):
        """Закрывает соединение с БД"""
        self.conn.close()


def main():
    """Точка входа для запуска генератора"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Генератор тестовых данных для CarWash Admin Pro')
    parser.add_argument('--clients', type=int, default=30, help='Количество клиентов (по умолчанию 30)')
    parser.add_argument('--orders', type=int, default=100, help='Количество заказов (по умолчанию 100)')
    parser.add_argument('--clear', action='store_true', help='Очистить существующие данные перед генерацией')
    
    args = parser.parse_args()
    
    generator = TestDataGenerator()
    
    if args.clear:
        print("⚠️ Очистка существующих данных...")
        generator.cursor.execute("DELETE FROM order_items")
        generator.cursor.execute("DELETE FROM orders")
        generator.cursor.execute("DELETE FROM clients")
        generator.cursor.execute("DELETE FROM consumable_usage")
        generator.conn.commit()
        print("   ✅ Данные очищены")
    
    generator.generate_all(clients=args.clients, orders=args.orders)
    generator.close()


if __name__ == "__main__":
    main()