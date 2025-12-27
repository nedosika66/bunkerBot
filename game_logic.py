import random
import string
from database import get_random_from_table, get_multiple_random

class Player:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        
        # Основні дані (БІОЛОГІЯ)
        self.gender = "Не визначено"
        self.age = 0
        self.childbearing = "Не визначено" # <--- НОВЕ
        
        # Характеристики
        self.profession = "Не визначено"
        self.profession_years = 0
        
        self.health = "Не визначено"
        self.health_severity = 0
        
        self.hobby = "Не визначено"
        self.hobby_years = 0
        
        self.phobia = "Не визначено"
        self.luggage = "Не визначено"
        self.facts = []
        
        self.revealed_attributes = [] 
        
    def generate_card(self):
        """Заповнює картку та генерує логічні числа."""
        # 1. ГЕНЕРАЦІЯ БІОЛОГІЇ
        self.gender = random.choice(["Чоловік", "Жінка"])
        self.age = random.randint(16, 75)
        
        # Шанс 80% на плідність
        if random.random() < 0.8:
            self.childbearing = "✅ Може мати дітей"
        else:
            self.childbearing = "🚫 Не може мати дітей"
        
        # 2. ТЯГНЕМО ТЕКСТ З БД
        prof = get_random_from_table('profession')
        heal = get_random_from_table('health')
        hobb = get_random_from_table('hobby')
        phob = get_random_from_table('phobia')
        lugg = get_random_from_table('luggage')
        facts_data = get_multiple_random('fact', 2)

        if prof: self.profession = prof
        if heal: self.health = heal
        if hobb: self.hobby = hobb
        if phob: self.phobia = phob
        if lugg: self.luggage = lugg
        
        if facts_data: self.facts = facts_data
        else: self.facts = ["Фактів немає", "Фактів немає"]

        # 3. ГЕНЕРУЄМО ЧИСЛА
        max_prof_years = max(0, self.age - 16)
        self.profession_years = random.randint(0, max_prof_years)
        
        max_hobby_years = max(0, self.age - 5)
        self.hobby_years = random.randint(0, max_hobby_years)
        
        self.health_severity = random.randint(1, 100)
            
        self.revealed_attributes = []

class Game:
    def __init__(self, chat_id, admin_id, admin_name):
        self.chat_id = chat_id
        self.admin_id = admin_id
        self.admin_name = admin_name
        self.players = {}
        self.is_active = False
        self.disaster_text = "Очікування..."
        self.votes = {} 
        
        chars = string.ascii_uppercase + string.digits
        self.invite_code = ''.join(random.choices(chars, k=6))

games = {}
games_by_invite = {}