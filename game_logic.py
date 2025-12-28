import random
import string
from database import get_random_from_table, get_multiple_random

games = {}
games_by_invite = {}

class Player:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name
        self.revealed_attributes = []
        
        self.gender = "Невідомо"
        self.age = 0
        self.childbearing = "Невідомо"
        self.profession = "Невідомо"
        self.profession_years = 0
        self.health = "Невідомо"
        self.health_severity = 0
        self.hobby = "Невідомо"
        self.hobby_years = 0
        self.phobia = "Невідомо"
        self.luggage = "Невідомо"
        self.facts = []

    def generate_card(self):
        self.gender = random.choice(["Чоловік", "Жінка"])
        self.age = random.randint(16, 75)

        base_status = random.choices(
            ["Здатний(а) до розмноження", "Безпліддя"], 
            weights=[75, 25], 
            k=1
        )[0]

        if self.gender == "Жінка" and self.age > 50:
            self.childbearing = "Безпліддя (Менопауза)"
        else:
            self.childbearing = base_status

        self.profession = get_random_from_table("profession")
        max_exp = max(0, self.age - 18) 
        self.profession_years = random.randint(0, max_exp)

        self.health = get_random_from_table("health")
        self.health_severity = random.randint(5, 100)

        self.hobby = get_random_from_table("hobby")
        self.hobby_years = random.randint(0, max(1, self.age - 10))

        self.phobia = get_random_from_table("phobia")
        self.luggage = get_random_from_table("luggage")
        self.facts = get_multiple_random("fact", count=2)

class Game:
    def __init__(self, chat_id, admin_id, admin_name):
        self.chat_id = chat_id
        self.admin_id = admin_id
        self.admin_name = admin_name
        self.players = {}
        self.is_active = False
        self.disaster_text = ""
        self.votes = {}
        self.invite_code = self._generate_code()
    
    def _generate_code(self):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

    def add_player(self, user_id, name):
        if user_id not in self.players:
            self.players[user_id] = Player(user_id, name)
