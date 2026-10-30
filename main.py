import pygame
import numpy as np
import random
import math
import json
import os
import sys
from datetime import datetime

# ==============================================================================
# ИНИЦИАЛИЗАЦИЯ PYGAME И АУДИО-СИНТЕЗАТОРА
# ==============================================================================
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    AUDIO_AVAILABLE = True
except Exception:
    AUDIO_AVAILABLE = False


class GameConfig:
    TITLE = "STAR PAWS: ГАЛАКТИЧЕСКИЙ КОТО-ПАТРУЛЬ [PRO MVP EDITION]"
    WIDTH = 1280
    HEIGHT = 720
    FPS = 60
    SAVE_FILE = "starpaws_save.json"

    # Цветовая палитра (RGB)
    BG_DARK = (10, 12, 28)
    BG_DEEP = (18, 20, 45)
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    CYAN = (0, 240, 255)
    NEON_BLUE = (50, 150, 255)
    NEON_GREEN = (50, 255, 120)
    NEON_YELLOW = (255, 230, 50)
    NEON_ORANGE = (255, 140, 40)
    NEON_RED = (255, 60, 90)
    NEON_PURPLE = (190, 70, 255)
    NEON_PINK = (255, 90, 200)
    GOLD = (255, 205, 0)
    GRAY = (130, 140, 160)
    DARK_GRAY = (40, 45, 65)


# ==============================================================================
# ПРОЦЕДУРНЫЙ ГЕНЕРАТОР ЗВУКОВ (БЕЗ ВНЕШНИХ MP3/WAV ФАЙЛОВ)
# ==============================================================================
class ProceduralSoundEngine:
    """Генерирует ретро-звуки и спецэффекты в реальном времени через NumPy."""
    def __init__(self):
        self.enabled = AUDIO_AVAILABLE
        self.sounds = {}
        self.sample_rate = 44100
        if self.enabled:
            self._build_sound_bank()

    def _make_sound(self, wave_array):
        wave_int16 = np.int16(wave_array * 32767)
        stereo = np.column_stack((wave_int16, wave_int16))
        return pygame.sndarray.make_sound(stereo)

    def _build_sound_bank(self):
        try:
            # 1. Выстрел бластера (короткий свип вниз)
            t = np.linspace(0, 0.11, int(self.sample_rate * 0.11), False)
            freq = np.linspace(950, 220, len(t))
            env = np.linspace(0.35, 0.01, len(t))
            wave = np.sin(2 * np.pi * freq * t) * env
            self.sounds["shoot"] = self._make_sound(wave)

            # 2. Плазменный залп
            t = np.linspace(0, 0.16, int(self.sample_rate * 0.16), False)
            freq = np.linspace(600, 120, len(t))
            env = np.linspace(0.4, 0.01, len(t))
            wave = np.sign(np.sin(2 * np.pi * freq * t)) * env * 0.5
            self.sounds["plasma"] = self._make_sound(wave)

            # 3. Сбор монетки / кристалла (двойной мажорный писк)
            t1 = np.linspace(0, 0.07, int(self.sample_rate * 0.07), False)
            t2 = np.linspace(0, 0.10, int(self.sample_rate * 0.10), False)
            w1 = np.sin(2 * np.pi * 987.77 * t1) * np.linspace(0.3, 0.1, len(t1))
            w2 = np.sin(2 * np.pi * 1318.51 * t2) * np.linspace(0.35, 0.01, len(t2))
            self.sounds["coin"] = self._make_sound(np.concatenate([w1, w2]))

            # 4. Взрыв врага (шум + низкая частота)
            t = np.linspace(0, 0.24, int(self.sample_rate * 0.24), False)
            noise = np.random.uniform(-1, 1, len(t))
            sub = np.sin(2 * np.pi * np.linspace(160, 40, len(t)) * t)
            env = np.linspace(0.45, 0.01, len(t)) ** 1.5
            self.sounds["explosion"] = self._make_sound((noise * 0.6 + sub * 0.4) * env)

            # 5. Получение урона
            t = np.linspace(0, 0.22, int(self.sample_rate * 0.22), False)
            freq = np.linspace(280, 90, len(t))
            wave = np.sign(np.sin(2 * np.pi * freq * t)) * np.linspace(0.45, 0.01, len(t))
            self.sounds["hit"] = self._make_sound(wave)

            # 6. Успешный ответ в викторине / Апгрейд
            notes = [523.25, 659.25, 783.99, 1046.50]
            parts = []
            for f in notes:
                tn = np.linspace(0, 0.08, int(self.sample_rate * 0.08), False)
                parts.append(np.sin(2 * np.pi * f * tn) * np.linspace(0.35, 0.05, len(tn)))
            self.sounds["powerup"] = self._make_sound(np.concatenate(parts))

            # 7. Ошибка / Неверный ответ
            t = np.linspace(0, 0.30, int(self.sample_rate * 0.30), False)
            w = (np.sin(2 * np.pi * 160 * t) + np.sin(2 * np.pi * 150 * t)) * 0.2
            self.sounds["wrong"] = self._make_sound(w * np.linspace(1.0, 0.05, len(t)))

            # 8. Сирена Босса
            t = np.linspace(0, 0.55, int(self.sample_rate * 0.55), False)
            freq = 320 + 140 * np.sin(2 * np.pi * 6 * t)
            wave = np.sin(2 * np.pi * freq * t) * 0.3
            self.sounds["boss_alarm"] = self._make_sound(wave)
        except Exception as e:
            print(f"[SOUND INIT WARNING]: {e}")
            self.enabled = False

    def play(self, name):
        if self.enabled and name in self.sounds:
            try:
                self.sounds[name].play()
            except Exception:
                pass


# ==============================================================================
# БАЗА ДАННЫХ ОБРАЗОВАТЕЛЬНЫХ КВЕСТОВ (МАТЕМАТИКА, КОСМОС, ЛОГИКА, АНГЛИЙСКИЙ)
# ==============================================================================
class EduQuizDatabase:
    """База вопросов, превращающая аркаду в продаваемый EdTech-продукт."""
    QUESTIONS = [
        {
            "category": "КОСМИЧЕСКАЯ МАТЕМАТИКА",
            "q": "Корабль пролетел 7 секторов по 8 световых лет. Сколько всего световых лет пройдено?",
            "answers": ["56", "48", "64", "54"],
            "correct": 0,
            "reward_desc": "+100 Кристаллов и Мега-Щит!"
        },
        {
            "category": "АСТРОНОМИЯ",
            "q": "Какая планета Солнечной системы самая большая?",
            "answers": ["Марс", "Юпитер", "Сатурн", "Нептун"],
            "correct": 1,
            "reward_desc": "+100 Кристаллов и Ускорение Огня!"
        },
        {
            "category": "АНГЛИЙСКИЙ ДЛЯ ПИЛОТОВ",
            "q": "Как переводится бортовая команда 'DESTROY THE ASTEROID'?",
            "answers": ["Починить корабль", "Уничтожить астероид", "Включить радар", "Покормить кота"],
            "correct": 1,
            "reward_desc": "+120 Кристаллов и Ремонт Корпуса!"
        },
        {
            "category": "КОСМИЧЕСКАЯ МАТЕМАТИКА",
            "q": "В отряде 3 корабля, на каждом по 15 энергетических батарей. Сколько батарей всего?",
            "answers": ["35", "40", "45", "50"],
            "correct": 2,
            "reward_desc": "+100 Кристаллов и Полное Здоровье!"
        },
        {
            "category": "НАУКА И ЛОГИКА",
            "q": "Какая звезда находится ближе всего к планете Земля?",
            "answers": ["Полярная звезда", "Сириус", "Солнце", "Альфа Центавра"],
            "correct": 2,
            "reward_desc": "+110 Кристаллов и Плазменный Залп!"
        },
        {
            "category": "АНГЛИЙСКИЙ ДЛЯ ПИЛОТОВ",
            "q": "На приборной панели горит 'SHIELD POWER LOW'. Что это значит?",
            "answers": ["Мало заряда щита", "Топливо на максимуме", "Враг побежден", "Открыть люк"],
            "correct": 0,
            "reward_desc": "+120 Кристаллов и Энергетический Щит!"
        },
        {
            "category": "КОСМИЧЕСКАЯ МАТЕМАТИКА",
            "q": "Реши уравнение для запуска гипердвигателя: 120 - (9 * 5) = ?",
            "answers": ["65", "75", "85", "70"],
            "correct": 1,
            "reward_desc": "+130 Кристаллов и Сверхзвуковой Рывок!"
        },
        {
            "category": "АСТРОНОМИЯ",
            "q": "Как называется галактика, в которой находится наша Солнечная система?",
            "answers": ["Андромеда", "Млечный Путь", "Туманность Кошки", "Большой Пёс"],
            "correct": 1,
            "reward_desc": "+100 Кристаллов и Усиление Оружия!"
        },
        {
            "category": "ЛОГИКА И ПРОГРАММИРОВАНИЕ",
            "q": "Робот выполняет цикл 4 раза: 'Сделать 3 шага вперёд'. Сколько шагов он сделает?",
            "answers": ["7", "10", "12", "16"],
            "correct": 2,
            "reward_desc": "+140 Кристаллов и Ремонт Дрона!"
        },
        {
            "category": "КОСМИЧЕСКАЯ МАТЕМАТИКА",
            "q": "У босса было 200 HP. Первый лазер снял 60 HP, а второй — ещё 55 HP. Сколько осталось?",
            "answers": ["85", "95", "75", "90"],
            "correct": 0,
            "reward_desc": "+150 Кристаллов и Сверхмощный Лазер!"
        },
        {
            "category": "АНГЛИЙСКИЙ ДЛЯ ПИЛОТОВ",
            "q": "Что означает слово 'TREASURE' на космической карте?",
            "answers": ["Опасность", "Сокровище", "Черная дыра", "Спутник"],
            "correct": 1,
            "reward_desc": "+150 Кристаллов и Золотой Бонус!"
        },
        {
            "category": "НАУКА И ФИЗИКА",
            "q": "Почему космонавты на орбитальной станции летают внутри корабля?",
            "answers": ["Из-за невесомости", "У них реактивные ботинки", "Там сильный ветер", "Пол из батута"],
            "correct": 0,
            "reward_desc": "+110 Кристаллов и Защита Корпуса!"
        }
    ]

    @classmethod
    def get_random_question(cls):
        base = random.choice(cls.QUESTIONS)
        # Также можем динамически генерировать математический пример в 40% случаев
        if random.random() < 0.4:
            a = random.randint(6, 15)
            b = random.randint(4, 12)
            op = random.choice(["*", "+"])
            if op == "*":
                ans = a * b
                q_str = f"Быстрый расчёт навигатора: сколько будет {a} × {b}?"
            else:
                c = random.randint(15, 50)
                ans = a * b + c
                q_str = f"Код доступа к кристаллу: ({a} × {b}) + {c} = ?"

            wrong_set = set()
            while len(wrong_set) < 3:
                candidate = ans + random.choice([-12, -10, -6, -4, -2, 2, 4, 6, 8, 10, 14])
                if candidate != ans and candidate > 0:
                    wrong_set.add(str(candidate))
            options = list(wrong_set) + [str(ans)]
            random.shuffle(options)
            return {
                "category": "БЫСТРЫЙ СЧЁТ НАВИГАТОРА",
                "q": q_str,
                "answers": options,
                "correct": options.index(str(ans)),
                "reward_desc": "+130 Кристаллов и Overdrive-режим!"
            }
        return base


# ==============================================================================
# СИСТЕМА СОХРАНЕНИЯ ПРОГРЕССА, МАГАЗИНА И ДОСТИЖЕНИЙ
# ==============================================================================
class SaveManager:
    DEFAULT_DATA = {
        "crystals": 250,
        "high_score": 0,
        "max_wave": 1,
        "total_kills": 0,
        "quizzes_solved": 0,
        "selected_skin": 0,
        "unlocked_skins": [0],
        "upgrades": {
            "hull_level": 1,       # Здоровье корабля
            "weapon_level": 1,     # Урон и количество стволов
            "speed_level": 1,      # Скорость двигателей
            "magnet_level": 1,     # Радиус притяжения кристаллов
            "pet_drone_level": 0   # Боевой питомец-дрон (0 - нет, 1..5 - уровень)
        },
        "achievements": {
            "first_blood": False,
            "scholar_cat": False,
            "boss_slayer": False,
            "rich_cat": False,
            "combo_master": False
        }
    }

    SKINS_CATALOG = [
        {
            "id": 0,
            "name": "КАПИТАН БАРСИК",
            "desc": "Сбалансированный крейсер Кото-Патруля",
            "price": 0,
            "primary": (0, 220, 255),
            "secondary": (255, 255, 255),
            "ear_color": (255, 130, 180),
            "bonus_text": "Стандартный корпус"
        },
        {
            "id": 1,
            "name": "НЕОНОВЫЙ ТИГР",
            "desc": "Ударный перехватчик с повышенным уроном (+15%)",
            "price": 400,
            "primary": (255, 145, 0),
            "secondary": (40, 40, 50),
            "ear_color": (255, 220, 60),
            "bonus_text": "+15% к урону пушек"
        },
        {
            "id": 2,
            "name": "КИБЕР-ПАНТЕРА X",
            "desc": "Стелс-корвет из темного сплава (+20% к скорости)",
            "price": 750,
            "primary": (185, 65, 255),
            "secondary": (25, 25, 45),
            "ear_color": (0, 255, 220),
            "bonus_text": "+20% к манёвренности"
        },
        {
            "id": 3,
            "name": "ЗОЛОТОЙ ЛЕВ ИМПЕРИИ",
            "desc": "Флагман галактики (+30% больше кристаллов и брони)",
            "price": 1200,
            "primary": (255, 210, 35),
            "secondary": (255, 250, 210),
            "ear_color": (255, 60, 80),
            "bonus_text": "+30% кристаллов и щит"
        }
    ]

    ACHIEVEMENTS_INFO = {
        "first_blood": ("Первая Победа", "Уничтожить 25 космических пиратов"),
        "scholar_cat": ("Кот-Учёный", "Ответить правильно на 5 вопросов щита знаний"),
        "boss_slayer": ("Гроза Боссов", "Победить Флагманского Босса сектора"),
        "rich_cat": ("Космический Магнат", "Накопить 1000 кристаллов в ангаре"),
        "combo_master": ("Мастер Комбо", "Набрать комбо x15 без потери здоровья")
    }

    def __init__(self):
        self.data = json.loads(json.dumps(self.DEFAULT_DATA))
        self.load()

    def load(self):
        if os.path.exists(GameConfig.SAVE_FILE):
            try:
                with open(GameConfig.SAVE_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    for k, v in loaded.items():
                        if isinstance(v, dict) and k in self.data:
                            self.data[k].update(v)
                        else:
                            self.data[k] = v
            except Exception as e:
                print(f"[SAVE LOAD ERROR]: {e}")

    def save(self):
        try:
            with open(GameConfig.SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[SAVE WRITE ERROR]: {e}")


# ==============================================================================
# ВИЗУАЛЬНЫЕ ЭФФЕКТЫ: ЧАСТИЦЫ, ВСПЛЫВАЮЩИЙ ТЕКСТ, ЗВЁЗДНОЕ НЕБО
# ==============================================================================
class Particle:
    def __init__(self, x, y, color, speed_range=(2, 8), size_range=(3, 7), life_range=(18, 40), glow=True):
        self.x = float(x)
        self.y = float(y)
        angle = random.uniform(0, math.pi * 2)
        spd = random.uniform(*speed_range)
        self.vx = math.cos(angle) * spd
        self.vy = math.sin(angle) * spd
        self.color = color
        self.size = random.uniform(*size_range)
        self.max_life = random.randint(*life_range)
        self.life = self.max_life
        self.glow = glow

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.96
        self.vy *= 0.96
        self.life -= 1
        return self.life > 0

    def draw(self, surface, ox=0, oy=0):
        ratio = max(0.0, self.life / self.max_life)
        r = max(1, int(self.size * ratio))
        px, py = int(self.x + ox), int(self.y + oy)
        if self.glow and r > 2:
            glow_col = (self.color[0] // 3, self.color[1] // 3, self.color[2] // 3)
            pygame.draw.circle(surface, glow_col, (px, py), r * 2)
        pygame.draw.circle(surface, self.color, (px, py), r)


class FloatingText:
    def __init__(self, x, y, text, color=GameConfig.NEON_YELLOW, size=22):
        self.x = float(x)
        self.y = float(y)
        self.text = str(text)
        self.color = color
        self.size = size
        self.life = 48
        self.max_life = 48

    def update(self):
        self.y -= 1.3
        self.life -= 1
        return self.life > 0

    def draw(self, surface, font):
        img = font.render(self.text, True, self.color)
        shadow = font.render(self.text, True, GameConfig.BLACK)
        surface.blit(shadow, (int(self.x) - img.get_width() // 2 + 2, int(self.y) + 2))
        surface.blit(img, (int(self.x) - img.get_width() // 2, int(self.y)))


class StarfieldBackground:
    """Многослойный параллакс-космос с туманностями и планетами."""
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.stars = []
        for layer in range(1, 4):
            count = 45 if layer == 1 else (30 if layer == 2 else 18)
            for _ in range(count):
                self.stars.append({
                    "x": random.uniform(0, w),
                    "y": random.uniform(0, h),
                    "speed": layer * 1.15,
                    "size": layer,
                    "color": random.choice([
                        (180, 200, 255),
                        (255, 240, 200),
                        (150, 255, 240),
                        (230, 180, 255)
                    ])
                })

        self.planets = [
            {"x": 220, "y": 140, "r": 52, "color": (70, 45, 120), "ring": True, "speed": 0.25},
            {"x": 980, "y": -180, "r": 38, "color": (35, 95, 130), "ring": False, "speed": 0.4}
        ]

    def update(self, speed_mult=1.0):
        for s in self.stars:
            s["y"] += s["speed"] * speed_mult
            if s["y"] > self.h:
                s["y"] = 0
                s["x"] = random.uniform(0, self.w)

        for p in self.planets:
            p["y"] += p["speed"] * speed_mult
            if p["y"] - p["r"] > self.h + 80:
                p["y"] = -120
                p["x"] = random.randint(120, self.w - 120)

    def draw(self, surface):
        surface.fill(GameConfig.BG_DARK)

        # Отрисовка далёких планет
        for p in self.planets:
            px, py, pr = int(p["x"]), int(p["y"]), p["r"]
            pygame.draw.circle(surface, p["color"], (px, py), pr)
            light_col = (min(255, p["color"][0] + 35), min(255, p["color"][1] + 35), min(255, p["color"][2] + 35))
            pygame.draw.circle(surface, light_col, (px - pr // 4, py - pr // 4), int(pr * 0.7))
            if p["ring"]:
                rect = pygame.Rect(px - int(pr * 1.7), py - int(pr * 0.35), int(pr * 3.4), int(pr * 0.7))
                pygame.draw.ellipse(surface, (140, 110, 190), rect, 3)

        # Отрисовка звёзд
        for s in self.stars:
            pygame.draw.circle(surface, s["color"], (int(s["x"]), int(s["y"])), s["size"])


# ==============================================================================
# ИГРОВЫЕ СУЩНОСТИ: ПУЛИ, КРИСТАЛЛЫ, БОНУСЫ, КОРАБЛЬ КОТА, ДРОН, ВРАГИ И БОССЫ
# ==============================================================================
class Bullet:
    def __init__(self, x, y, vx, vy, damage, color=GameConfig.CYAN, radius=6, is_player=True, homing=False):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.damage = damage
        self.color = color
        self.radius = radius
        self.is_player = is_player
        self.homing = homing
        self.alive = True

    def update(self, enemies=None):
        if self.homing and enemies:
            # Самонаведение для ракет и дронов
            nearest = None
            min_d = 450.0
            for e in enemies:
                d = math.hypot(e.x - self.x, e.y - self.y)
                if d < min_d:
                    min_d = d
                    nearest = e
            if nearest:
                desired_angle = math.atan2(nearest.y - self.y, nearest.x - self.x)
                spd = math.hypot(self.vx, self.vy)
                self.vx = self.vx * 0.88 + math.cos(desired_angle) * spd * 0.12
                self.vy = self.vy * 0.88 + math.sin(desired_angle) * spd * 0.12

        self.x += self.vx
        self.y += self.vy
        if self.x < -40 or self.x > GameConfig.WIDTH + 40 or self.y < -40 or self.y > GameConfig.HEIGHT + 40:
            self.alive = False

    def draw(self, surface, ox=0, oy=0):
        px, py = int(self.x + ox), int(self.y + oy)
        glow_col = (self.color[0] // 3, self.color[1] // 3, self.color[2] // 3)
        pygame.draw.circle(surface, glow_col, (px, py), self.radius + 4)
        pygame.draw.circle(surface, self.color, (px, py), self.radius)
        pygame.draw.circle(surface, GameConfig.WHITE, (px, py), max(2, self.radius // 2))


class LootDrop:
    """Кристаллы, аптечки, сундуки знаний и усилители оружия."""
    def __init__(self, x, y, kind="crystal", value=10):
        self.x = float(x)
        self.y = float(y)
        self.kind = kind  # "crystal", "heal", "overdrive", "edu_chest"
        self.value = value
        self.vy = random.uniform(1.4, 2.5)
        self.vx = random.uniform(-1.0, 1.0)
        self.phase = random.uniform(0, 6.28)
        self.alive = True

    def update(self, player):
        self.phase += 0.12
        dist = math.hypot(player.x - self.x, player.y - self.y)
        if dist < player.magnet_radius:
            angle = math.atan2(player.y - self.y, player.x - self.x)
            pull_spd = 9.5
            self.x += math.cos(angle) * pull_spd
            self.y += math.sin(angle) * pull_spd
        else:
            self.x += self.vx
            self.y += self.vy
            self.vx *= 0.98

        if self.y > GameConfig.HEIGHT + 40:
            self.alive = False

    def draw(self, surface, ox=0, oy=0):
        px = int(self.x + ox)
        py = int(self.y + oy + math.sin(self.phase) * 4)

        if self.kind == "crystal":
            pts = [(px, py - 11), (px + 9, py), (px, py + 11), (px - 9, py)]
            pygame.draw.polygon(surface, GameConfig.CYAN, pts)
            pygame.draw.polygon(surface, GameConfig.WHITE, pts, 2)
        elif self.kind == "heal":
            pygame.draw.circle(surface, GameConfig.NEON_GREEN, (px, py), 13)
            pygame.draw.rect(surface, GameConfig.WHITE, (px - 3, py - 8, 6, 16))
            pygame.draw.rect(surface, GameConfig.WHITE, (px - 8, py - 3, 16, 6))
        elif self.kind == "overdrive":
            pygame.draw.circle(surface, GameConfig.NEON_ORANGE, (px, py), 14)
            pygame.draw.circle(surface, GameConfig.NEON_YELLOW, (px, py), 9)
        elif self.kind == "edu_chest":
            rect = pygame.Rect(px - 16, py - 12, 32, 24)
            pygame.draw.rect(surface, GameConfig.NEON_PURPLE, rect, border_radius=5)
            pygame.draw.rect(surface, GameConfig.GOLD, rect, 3, border_radius=5)
            pygame.draw.circle(surface, GameConfig.NEON_YELLOW, (px, py), 5)


class PlayerCatShip:
    """Космический корабль с котом-пилотом в стеклянном куполе и боевым дроном."""
    def __init__(self, save_mgr):
        self.save_mgr = save_mgr
        self.x = float(GameConfig.WIDTH // 2)
        self.y = float(GameConfig.HEIGHT - 110)
        self.radius = 28

        # Применение прокачки и бонусов скина
        up = save_mgr.data["upgrades"]
        skin_id = save_mgr.data["selected_skin"]
        self.skin = SaveManager.SKINS_CATALOG[skin_id]

        self.max_hp = 100 + (up["hull_level"] - 1) * 35 + (30 if skin_id == 3 else 0)
        self.hp = self.max_hp
        self.max_shield = 60 + (up["hull_level"] - 1) * 20
        self.shield = self.max_shield

        base_spd = 6.2 + (up["speed_level"] - 1) * 0.75
        self.speed = base_spd * (1.2 if skin_id == 2 else 1.0)

        self.weapon_level = up["weapon_level"]
        self.damage_mult = 1.15 if skin_id == 1 else 1.0
        self.crystal_mult = 1.30 if skin_id == 3 else 1.0
        self.magnet_radius = 120 + (up["magnet_level"] - 1) * 45
        self.pet_level = up["pet_drone_level"]

        self.shoot_timer = 0
        self.overdrive_timer = 0
        self.invulnerable_timer = 0
        self.pet_angle = 0.0
        self.pet_shoot_timer = 0
        self.engine_flicker = 0.0

    def update(self, keys, mouse_pos, mouse_pressed, bullets, enemies, sound_eng):
        self.engine_flicker += 0.35
        self.pet_angle += 0.06

        if self.overdrive_timer > 0:
            self.overdrive_timer -= 1
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

        # Медленная регенерация энергетического щита
        if self.shield < self.max_shield:
            self.shield = min(self.max_shield, self.shield + 0.06)

        # Движение с клавиатуры (WASD или Стрелки)
        dx, dy = 0.0, 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        self.x += dx * self.speed
        self.y += dy * self.speed

        # Ограничение в пределах экрана
        self.x = max(45, min(GameConfig.WIDTH - 45, self.x))
        self.y = max(75, min(GameConfig.HEIGHT - 55, self.y))

        # Автострельба или стрельба по пробелу / ЛКМ
        self.shoot_timer -= 1
        if (keys[pygame.K_SPACE] or mouse_pressed[0] or True) and self.shoot_timer <= 0:
            self.fire_weapons(bullets, sound_eng)

        # Стрельба питомца-дрона
        if self.pet_level > 0:
            self.pet_shoot_timer -= 1
            if self.pet_shoot_timer <= 0 and len(enemies) > 0:
                px = self.x + math.cos(self.pet_angle) * 58
                py = self.y + math.sin(self.pet_angle) * 58
                dmg = (12 + self.pet_level * 5) * self.damage_mult
                bullets.append(Bullet(px, py, 0, -11, dmg, GameConfig.NEON_GREEN, 5, True, homing=True))
                self.pet_shoot_timer = max(14, 34 - self.pet_level * 4)

    def fire_weapons(self, bullets, sound_eng):
        over = self.overdrive_timer > 0
        cooldown = 7 if over else max(8, 15 - self.weapon_level)
        self.shoot_timer = cooldown

        base_dmg = (16 + self.weapon_level * 4) * self.damage_mult
        if over:
            base_dmg *= 1.35

        lvl = self.weapon_level + (2 if over else 0)
        col = GameConfig.NEON_YELLOW if over else self.skin["primary"]

        if lvl == 1:
            bullets.append(Bullet(self.x, self.y - 28, 0, -14, base_dmg, col, 6))
        elif lvl == 2:
            bullets.append(Bullet(self.x - 14, self.y - 20, 0, -14, base_dmg, col, 6))
            bullets.append(Bullet(self.x + 14, self.y - 20, 0, -14, base_dmg, col, 6))
        elif lvl == 3:
            bullets.append(Bullet(self.x, self.y - 30, 0, -15, base_dmg * 1.1, col, 7))
            bullets.append(Bullet(self.x - 18, self.y - 18, -1.8, -13.5, base_dmg, col, 6))
            bullets.append(Bullet(self.x + 18, self.y - 18, 1.8, -13.5, base_dmg, col, 6))
        elif lvl == 4:
            for vx in (-3.2, -1.1, 1.1, 3.2):
                bullets.append(Bullet(self.x + vx * 5, self.y - 22, vx, -14, base_dmg, col, 6))
        else:
            # Веерный залп + самонаводящиеся плазменные сферы
            for vx in (-4.5, -2.2, 0, 2.2, 4.5):
                bullets.append(Bullet(self.x + vx * 4, self.y - 24, vx, -15, base_dmg, col, 7))
            bullets.append(Bullet(self.x - 28, self.y, -4, -10, base_dmg * 0.8, GameConfig.NEON_PINK, 6, True, homing=True))
            bullets.append(Bullet(self.x + 28, self.y, 4, -10, base_dmg * 0.8, GameConfig.NEON_PINK, 6, True, homing=True))

        sound_eng.play("shoot")

    def take_damage(self, amount, sound_eng):
        if self.invulnerable_timer > 0:
            return False
        self.invulnerable_timer = 25
        sound_eng.play("hit")

        if self.shield > 0:
            absorbed = min(self.shield, amount)
            self.shield -= absorbed
            rem = amount - absorbed
            self.hp -= rem
        else:
            self.hp -= amount
        return True

    def draw(self, surface, ox=0, oy=0):
        px, py = int(self.x + ox), int(self.y + oy)

        # Мерцание при неуязвимости
        if self.invulnerable_timer > 0 and (self.invulnerable_timer // 3) % 2 == 0:
            return

        # 1. Пламя реактивного двигателя
        flame_len = int(18 + math.sin(self.engine_flicker) * 7 + (10 if self.overdrive_timer > 0 else 0))
        pygame.draw.polygon(surface, GameConfig.NEON_ORANGE, [
            (px - 12, py + 20), (px + 12, py + 20), (px, py + 20 + flame_len)
        ])
        pygame.draw.polygon(surface, GameConfig.NEON_YELLOW, [
            (px - 6, py + 20), (px + 6, py + 20), (px, py + 14 + flame_len)
        ])

        # 2. Крылья космолёта
        wing_pts = [
            (px, py - 34),
            (px - 38, py + 22),
            (px - 14, py + 16),
            (px + 14, py + 16),
            (px + 38, py + 22)
        ]
        pygame.draw.polygon(surface, self.skin["primary"], wing_pts)
        pygame.draw.polygon(surface, GameConfig.WHITE, wing_pts, 2)

        # Боковые пушки
        pygame.draw.rect(surface, self.skin["secondary"], (px - 32, py - 6, 6, 20), border_radius=2)
        pygame.draw.rect(surface, self.skin["secondary"], (px + 26, py - 6, 6, 20), border_radius=2)

        # 3. Кабина с Котом-Пилотом внутри
        pygame.draw.circle(surface, (30, 45, 70), (px, py - 2), 17)
        # Ушки кота
        pygame.draw.polygon(surface, self.skin["ear_color"], [(px - 13, py - 8), (px - 16, py - 21), (px - 4, py - 13)])
        pygame.draw.polygon(surface, self.skin["ear_color"], [(px + 13, py - 8), (px + 16, py - 21), (px + 4, py - 13)])
        # Голова кота
        pygame.draw.circle(surface, self.skin["secondary"], (px, py - 2), 12)
        # Глазки и носик кота
        pygame.draw.circle(surface, GameConfig.BLACK, (px - 4, py - 4), 2)
        pygame.draw.circle(surface, GameConfig.BLACK, (px + 4, py - 4), 2)
        pygame.draw.polygon(surface, (255, 110, 150), [(px - 2, py), (px + 2, py), (px, py + 3)])

        # Стеклянный блик купола
        pygame.draw.circle(surface, GameConfig.CYAN, (px, py - 2), 17, 2)

        # 4. Энергетический щит вокруг корабля
        if self.shield > 5:
            pygame.draw.circle(surface, (0, 200, 255), (px, py), 38, 1)

        # 5. Отрисовка боевого питомца-дрона
        if self.pet_level > 0:
            dx = int(px + math.cos(self.pet_angle) * 58)
            dy = int(py + math.sin(self.pet_angle) * 58)
            pygame.draw.circle(surface, GameConfig.NEON_GREEN, (dx, dy), 10)
            pygame.draw.circle(surface, GameConfig.WHITE, (dx, dy), 10, 2)
            # Маленькие ушки дрона
            pygame.draw.polygon(surface, GameConfig.NEON_GREEN, [(dx - 8, dy - 6), (dx - 10, dy - 14), (dx - 2, dy - 9)])
            pygame.draw.polygon(surface, GameConfig.NEON_GREEN, [(dx + 8, dy - 6), (dx + 10, dy - 14), (dx + 2, dy - 9)])


class EnemyShip:
    """Вражеские корабли: Робо-Мыши, Кибер-Псы, Астероиды и Боссы Секторов."""
    def __init__(self, wave, kind="mouse_scout"):
        self.kind = kind
        self.wave = wave
        self.x = float(random.randint(70, GameConfig.WIDTH - 70))
        self.y = float(random.randint(-90, -35))
        self.phase = random.uniform(0, 6.28)
        self.shoot_timer = random.randint(45, 110)
        self.alive = True
        self.is_boss = False

        if kind == "mouse_scout":
            self.name = "Робо-Мышь Разведчик"
            self.radius = 22
            self.max_hp = 28 + wave * 9
            self.speed = random.uniform(2.2, 3.4)
            self.color = GameConfig.NEON_RED
            self.score_val = 25
        elif kind == "astro_dog":
            self.name = "Кибер-Бульдог Штурмовик"
            self.radius = 28
            self.max_hp = 55 + wave * 16
            self.speed = random.uniform(1.6, 2.4)
            self.color = GameConfig.NEON_ORANGE
            self.score_val = 45
        elif kind == "ufo_sniper":
            self.name = "Снайперский Дрон НЛО"
            self.radius = 24
            self.max_hp = 40 + wave * 12
            self.speed = random.uniform(1.8, 2.6)
            self.color = GameConfig.NEON_PURPLE
            self.score_val = 40
        elif kind == "boss":
            self.is_boss = True
            self.name = f"ФЛАГМАН КИБЕР-ПСОВ [СЕКТОР {wave}]"
            self.x = float(GameConfig.WIDTH // 2)
            self.y = -80.0
            self.radius = 68
            self.max_hp = 550 + wave * 240
            self.speed = 2.2
            self.color = GameConfig.NEON_PINK
            self.score_val = 500

        self.hp = self.max_hp

    def update(self, player, enemy_bullets):
        self.phase += 0.05

        if self.is_boss:
            if self.y < 135:
                self.y += 1.8
            else:
                self.x += math.cos(self.phase * 0.7) * 4.2
                self.x = max(110, min(GameConfig.WIDTH - 110, self.x))

            self.shoot_timer -= 1
            if self.shoot_timer <= 0:
                self.shoot_timer = max(32, 65 - self.wave * 3)
                # Круговой или веерный залп босса
                for angle_deg in range(35, 150, 22):
                    rad = math.radians(angle_deg)
                    vx = math.cos(rad) * 5.8
                    vy = math.sin(rad) * 5.8
                    enemy_bullets.append(Bullet(self.x, self.y + 40, vx, vy, 18, GameConfig.NEON_RED, 7, is_player=False))
        else:
            self.y += self.speed
            if self.kind == "mouse_scout":
                self.x += math.sin(self.phase * 1.4) * 2.5
            elif self.kind == "ufo_sniper":
                self.x += math.cos(self.phase) * 3.2

            self.x = max(40, min(GameConfig.WIDTH - 40, self.x))

            self.shoot_timer -= 1
            if self.shoot_timer <= 0 and self.y > 40 and self.y < GameConfig.HEIGHT - 220:
                self.shoot_timer = random.randint(75, 140)
                if self.kind == "ufo_sniper":
                    ang = math.atan2(player.y - self.y, player.x - self.x)
                    enemy_bullets.append(Bullet(self.x, self.y, math.cos(ang) * 6.5, math.sin(ang) * 6.5, 14, GameConfig.NEON_PURPLE, 6, False))
                elif self.kind == "astro_dog":
                    enemy_bullets.append(Bullet(self.x - 12, self.y + 15, 0, 5.5, 12, GameConfig.NEON_ORANGE, 6, False))
                    enemy_bullets.append(Bullet(self.x + 12, self.y + 15, 0, 5.5, 12, GameConfig.NEON_ORANGE, 6, False))

        if self.y > GameConfig.HEIGHT + 65:
            self.alive = False

    def draw(self, surface, ox=0, oy=0):
        px, py = int(self.x + ox), int(self.y + oy)

        if self.is_boss:
            # Отрисовка гигантского Флагмана Босса
            rect = pygame.Rect(px - 75, py - 45, 150, 90)
            pygame.draw.rect(surface, (55, 20, 65), rect, border_radius=18)
            pygame.draw.rect(surface, self.color, rect, 4, border_radius=18)
            # Рога/антенны босса
            pygame.draw.polygon(surface, GameConfig.NEON_RED, [(px - 60, py - 45), (px - 85, py - 80), (px - 35, py - 45)])
            pygame.draw.polygon(surface, GameConfig.NEON_RED, [(px + 60, py - 45), (px + 85, py - 80), (px + 35, py - 45)])
            # Светящиеся глаза робо-босса
            pygame.draw.circle(surface, GameConfig.NEON_YELLOW, (px - 28, py - 8), 14)
            pygame.draw.circle(surface, GameConfig.NEON_RED, (px - 28, py - 8), 7)
            pygame.draw.circle(surface, GameConfig.NEON_YELLOW, (px + 28, py - 8), 14)
            pygame.draw.circle(surface, GameConfig.NEON_RED, (px + 28, py - 8), 7)
            # Пушка по центру
            pygame.draw.rect(surface, GameConfig.GRAY, (px - 22, py + 22, 44, 18), border_radius=4)
        else:
            # Обычные вражеские корабли
            pygame.draw.circle(surface, (40, 25, 45), (px, py), self.radius)
            pygame.draw.circle(surface, self.color, (px, py), self.radius, 3)
            # Уши мыши или крылья дрона
            pygame.draw.circle(surface, self.color, (px - self.radius + 4, py - self.radius + 6), 9)
            pygame.draw.circle(surface, self.color, (px + self.radius - 4, py - self.radius + 6), 9)
            # Злые глазки
            pygame.draw.circle(surface, GameConfig.NEON_YELLOW, (px - 7, py - 2), 4)
            pygame.draw.circle(surface, GameConfig.NEON_YELLOW, (px + 7, py - 2), 4)

            # Полоска здоровья над раненым врагом
            if self.hp < self.max_hp:
                bw = 42
                pct = max(0.0, self.hp / self.max_hp)
                pygame.draw.rect(surface, GameConfig.DARK_GRAY, (px - bw // 2, py - self.radius - 12, bw, 5))
                pygame.draw.rect(surface, GameConfig.NEON_RED, (px - bw // 2, py - self.radius - 12, int(bw * pct), 5))


# ==============================================================================
# UI-КОМПОНЕНТЫ: НЕОНОВЫЕ КНОПКИ
# ==============================================================================
class NeonButton:
    def __init__(self, x, y, w, h, text, color=GameConfig.CYAN):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hovered = False

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)
        return self.hovered

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

    def draw(self, surface, font):
        bg_col = (self.color[0] // 4, self.color[1] // 4, self.color[2] // 4) if self.hovered else (20, 26, 48)
        border_w = 3 if self.hovered else 2
        pygame.draw.rect(surface, bg_col, self.rect, border_radius=10)
        pygame.draw.rect(surface, self.color, self.rect, border_w, border_radius=10)

        txt_col = GameConfig.WHITE if self.hovered else self.color
        txt_surf = font.render(self.text, True, txt_col)
        surface.blit(
            txt_surf,
            (self.rect.centerx - txt_surf.get_width() // 2, self.rect.centery - txt_surf.get_height() // 2)
        )


# ==============================================================================
# ГЛАВНЫЙ ДВИЖОК ИГРЫ: УПРАВЛЕНИЕ СЦЕНАМИ, БОЕМ, ВИКТОРИНОЙ И МАГАЗИНОМ
# ==============================================================================
class StarPawsGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((GameConfig.WIDTH, GameConfig.HEIGHT))
        pygame.display.set_caption(GameConfig.TITLE)
        self.clock = pygame.time.Clock()

        # Шрифты с поддержкой кириллицы
        self.font_xs = pygame.font.SysFont("arial", 15, bold=True)
        self.font_sm = pygame.font.SysFont("arial", 19, bold=True)
        self.font_md = pygame.font.SysFont("arial", 25, bold=True)
        self.font_lg = pygame.font.SysFont("arial", 36, bold=True)
        self.font_xl = pygame.font.SysFont("arial", 52, bold=True)

        self.sound = ProceduralSoundEngine()
        self.save_mgr = SaveManager()
        self.starfield = StarfieldBackground(GameConfig.WIDTH, GameConfig.HEIGHT)

        # Состояния: "MENU", "HANGAR", "PLAYING", "EDU_QUIZ", "GAME_OVER"
        self.state = "MENU"
        self.screen_shake = 0
        self.achievement_banner = None
        self.achievement_timer = 0

        self._init_menu_ui()
        self._init_hangar_ui()
        self.reset_combat_session()

    def _init_menu_ui(self):
        cx = GameConfig.WIDTH // 2
        self.btn_play = NeonButton(cx - 170, 290, 340, 58, "В БОЙ! (СТАРТ МИССИИ)", GameConfig.NEON_GREEN)
        self.btn_hangar = NeonButton(cx - 170, 368, 340, 58, "АНГАР И МАГАЗИН СКИНОВ", GameConfig.CYAN)
        self.btn_quiz_train = NeonButton(cx - 170, 446, 340, 58, "ТРЕНИРОВКА ЩИТА ЗНАНИЙ", GameConfig.NEON_PURPLE)
        self.btn_quit = NeonButton(cx - 170, 524, 340, 54, "ВЫХОД НА БАЗУ", GameConfig.NEON_RED)

    def _init_hangar_ui(self):
        self.btn_back_menu = NeonButton(40, 30, 210, 48, "< В ГЛАВНОЕ МЕНЮ", GameConfig.CYAN)
        self.upgrade_buttons = {}
        keys = ["hull_level", "weapon_level", "speed_level", "magnet_level", "pet_drone_level"]
        for i, k in enumerate(keys):
            self.upgrade_buttons[k] = NeonButton(460, 175 + i * 82, 195, 48, "УЛУЧШИТЬ", GameConfig.NEON_GREEN)

        self.skin_buttons = []
        for i in range(len(SaveManager.SKINS_CATALOG)):
            self.skin_buttons.append(NeonButton(1030, 175 + i * 115, 185, 48, "ВЫБРАТЬ", GameConfig.GOLD))

    def reset_combat_session(self):
        self.player = PlayerCatShip(self.save_mgr)
        self.player_bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.loot_items = []
        self.particles = []
        self.floating_texts = []

        self.score = 0
        self.session_crystals = 0
        self.wave = 1
        self.wave_kills = 0
        self.wave_target_kills = 10
        self.spawn_timer = 30
        self.boss_active = False

        self.combo = 1
        self.combo_timer = 0
        self.active_quiz = None
        self.quiz_buttons = []
        self.quiz_feedback_timer = 0
        self.quiz_feedback_text = ""
        self.quiz_from_menu = False

    def unlock_achievement(self, ach_key):
        if not self.save_mgr.data["achievements"].get(ach_key, False):
            self.save_mgr.data["achievements"][ach_key] = True
            title, desc = SaveManager.ACHIEVEMENTS_INFO[ach_key]
            self.achievement_banner = f"ДОСТИЖЕНИЕ ОТКРЫТО: {title} ({desc})"
            self.achievement_timer = 210
            self.save_mgr.data["crystals"] += 150
            self.save_mgr.save()
            self.sound.play("powerup")

    def spawn_explosion(self, x, y, color, count=24):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def start_edu_quiz(self, from_menu=False):
        self.quiz_from_menu = from_menu
        self.active_quiz = EduQuizDatabase.get_random_question()
        self.quiz_buttons = []
        cx = GameConfig.WIDTH // 2
        for i, ans_text in enumerate(self.active_quiz["answers"]):
            bx = cx - 290 if i % 2 == 0 else cx + 20
            by = 360 if i < 2 else 445
            self.quiz_buttons.append(NeonButton(bx, by, 270, 62, f"{i + 1}. {ans_text}", GameConfig.CYAN))
        self.quiz_feedback_timer = 0
        self.quiz_feedback_text = ""
        self.state = "EDU_QUIZ"

    # --------------------------------------------------------------------------
    # ОБНОВЛЕНИЕ БОЕВОЙ СЦЕНЫ
    # --------------------------------------------------------------------------
    def update_playing(self):
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()

        self.starfield.update(speed_mult=1.8 if self.player.overdrive_timer > 0 else 1.0)
        if self.screen_shake > 0:
            self.screen_shake -= 1

        if self.combo_timer > 0:
            self.combo_timer -= 1
        else:
            self.combo = 1

        # Обновление корабля игрока
        self.player.update(keys, mouse_pos, mouse_pressed, self.player_bullets, self.enemies, self.sound)

        # Спавн врагов и боссов
        self.spawn_timer -= 1
        if self.spawn_timer <= 0 and not self.boss_active:
            if self.wave_kills >= self.wave_target_kills:
                # Переход на следующую волну
                self.wave += 1
                self.wave_kills = 0
                self.wave_target_kills = 10 + self.wave * 4
                self.save_mgr.data["max_wave"] = max(self.save_mgr.data["max_wave"], self.wave)

                # Каждые 3 волны — Босс, а между ними — образовательный сундук знаний
                if self.wave % 3 == 0:
                    boss = EnemyShip(self.wave, kind="boss")
                    self.enemies.append(boss)
                    self.boss_active = True
                    self.sound.play("boss_alarm")
                    self.floating_texts.append(FloatingText(GameConfig.WIDTH // 2, 180, "ВНИМАНИЕ: ФЛАГМАН БОССА!", GameConfig.NEON_RED, 30))
                else:
                    self.loot_items.append(LootDrop(GameConfig.WIDTH // 2, 60, kind="edu_chest"))
                    self.floating_texts.append(FloatingText(GameConfig.WIDTH // 2, 140, f"СЕКТОР {self.wave} ОЧИЩЕН! БОНУС ЗНАНИЙ!", GameConfig.NEON_GREEN, 26))
            else:
                kinds = ["mouse_scout", "mouse_scout", "astro_dog", "ufo_sniper"]
                chosen = random.choice(kinds)
                self.enemies.append(EnemyShip(self.wave, kind=chosen))
                self.spawn_timer = max(20, 58 - self.wave * 3)

        # Обновление пуль игрока
        for b in self.player_bullets:
            b.update(self.enemies)
        self.player_bullets = [b for b in self.player_bullets if b.alive]

        # Обновление пуль врагов
        for b in self.enemy_bullets:
            b.update()
            if math.hypot(b.x - self.player.x, b.y - self.player.y) < self.player.radius + b.radius - 4:
                b.alive = False
                if self.player.take_damage(b.damage, self.sound):
                    self.screen_shake = 10
                    self.combo = 1
                    self.spawn_explosion(self.player.x, self.player.y, GameConfig.NEON_RED, 14)
        self.enemy_bullets = [b for b in self.enemy_bullets if b.alive]

        # Обновление врагов и проверка попаданий
        for e in self.enemies:
            e.update(self.player, self.enemy_bullets)

            # Столкновение врага с игроком
            if math.hypot(e.x - self.player.x, e.y - self.player.y) < e.radius + self.player.radius - 6:
                if not e.is_boss:
                    e.hp = 0
                if self.player.take_damage(24, self.sound):
                    self.screen_shake = 14
                    self.combo = 1
                    self.spawn_explosion(self.player.x, self.player.y, GameConfig.NEON_ORANGE, 20)

            # Попадание пуль игрока по врагу
            for b in self.player_bullets:
                if b.alive and math.hypot(b.x - e.x, b.y - e.y) < e.radius + b.radius:
                    b.alive = False
                    e.hp -= b.damage
                    self.particles.append(Particle(b.x, b.y, GameConfig.NEON_YELLOW, (1, 4), (2, 4), (8, 15)))

            if e.hp <= 0 and e.alive:
                e.alive = False
                self.sound.play("explosion")
                self.spawn_explosion(e.x, e.y, e.color, 38 if e.is_boss else 22)

                self.wave_kills += 1
                self.combo = min(25, self.combo + 1)
                self.combo_timer = 190
                pts = e.score_val * self.combo
                self.score += pts
                self.floating_texts.append(FloatingText(e.x, e.y, f"+{pts} (x{self.combo})", GameConfig.NEON_YELLOW))

                self.save_mgr.data["total_kills"] += 1
                if self.save_mgr.data["total_kills"] >= 25:
                    self.unlock_achievement("first_blood")
                if self.combo >= 15:
                    self.unlock_achievement("combo_master")

                # Выпадение кристаллов и бонусов
                if e.is_boss:
                    self.boss_active = False
                    self.unlock_achievement("boss_slayer")
                    for _ in range(12):
                        self.loot_items.append(LootDrop(e.x + random.randint(-45, 45), e.y + random.randint(-30, 30), "crystal", 25))
                    self.loot_items.append(LootDrop(e.x, e.y, "edu_chest"))
                else:
                    self.loot_items.append(LootDrop(e.x, e.y, "crystal", int(10 * self.player.crystal_mult)))
                    roll = random.random()
                    if roll < 0.09:
                        self.loot_items.append(LootDrop(e.x + 15, e.y, "heal"))
                    elif roll < 0.15:
                        self.loot_items.append(LootDrop(e.x - 15, e.y, "overdrive"))
                    elif roll < 0.20:
                        self.loot_items.append(LootDrop(e.x, e.y, "edu_chest"))

        self.enemies = [e for e in self.enemies if e.alive]

        # Сбор кристаллов и бонусов
        for item in self.loot_items:
            item.update(self.player)
            if math.hypot(item.x - self.player.x, item.y - self.player.y) < self.player.radius + 18:
                item.alive = False
                if item.kind == "crystal":
                    self.sound.play("coin")
                    self.session_crystals += item.value
                    self.save_mgr.data["crystals"] += item.value
                    if self.save_mgr.data["crystals"] >= 1000:
                        self.unlock_achievement("rich_cat")
                elif item.kind == "heal":
                    self.sound.play("powerup")
                    self.player.hp = min(self.player.max_hp, self.player.hp + 40)
                    self.floating_texts.append(FloatingText(self.player.x, self.player.y - 20, "+40 HP РЕМОНТ!", GameConfig.NEON_GREEN))
                elif item.kind == "overdrive":
                    self.sound.play("powerup")
                    self.player.overdrive_timer = 320
                    self.floating_texts.append(FloatingText(self.player.x, self.player.y - 20, "УЛЬТРА-ОРУЖИЕ!", GameConfig.NEON_ORANGE))
                elif item.kind == "edu_chest":
                    self.sound.play("powerup")
                    self.start_edu_quiz(from_menu=False)

        self.loot_items = [i for i in self.loot_items if i.alive]
        self.particles = [p for p in self.particles if p.update()]
        self.floating_texts = [ft for ft in self.floating_texts if ft.update()]

        # Проверка поражения
        if self.player.hp <= 0:
            self.save_mgr.data["high_score"] = max(self.save_mgr.data["high_score"], self.score)
            self.save_mgr.save()
            self.state = "GAME_OVER"

    # --------------------------------------------------------------------------
    # ОТРИСОВКА БОЕВОЙ СЦЕНЫ И ИНТЕРФЕЙСА
    # --------------------------------------------------------------------------
    def draw_playing(self):
        ox = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0
        oy = random.randint(-self.screen_shake, self.screen_shake) if self.screen_shake > 0 else 0

        self.starfield.draw(self.screen)

        for item in self.loot_items:
            item.draw(self.screen, ox, oy)
        for b in self.player_bullets:
            b.draw(self.screen, ox, oy)
        for b in self.enemy_bullets:
            b.draw(self.screen, ox, oy)
        for e in self.enemies:
            e.draw(self.screen, ox, oy)

        self.player.draw(self.screen, ox, oy)

        for p in self.particles:
            p.draw(self.screen, ox, oy)
        for ft in self.floating_texts:
            ft.draw(self.screen, self.font_sm)

        # Верхняя приборная панель HUD
        pygame.draw.rect(self.screen, (14, 18, 38), (0, 0, GameConfig.WIDTH, 64))
        pygame.draw.line(self.screen, GameConfig.CYAN, (0, 64), (GameConfig.WIDTH, 64), 2)

        # Полоска здоровья и щита
        hp_pct = max(0.0, self.player.hp / self.player.max_hp)
        sh_pct = max(0.0, self.player.shield / self.player.max_shield)
        pygame.draw.rect(self.screen, GameConfig.DARK_GRAY, (20, 14, 220, 18), border_radius=5)
        pygame.draw.rect(self.screen, GameConfig.NEON_GREEN, (20, 14, int(220 * hp_pct), 18), border_radius=5)
        hp_txt = self.font_xs.render(f"КОРПУС: {int(self.player.hp)}/{self.player.max_hp}", True, GameConfig.WHITE)
        self.screen.blit(hp_txt, (28, 14))

        pygame.draw.rect(self.screen, GameConfig.DARK_GRAY, (20, 38, 220, 14), border_radius=4)
        pygame.draw.rect(self.screen, GameConfig.CYAN, (20, 38, int(220 * sh_pct), 14), border_radius=4)
        sh_txt = self.font_xs.render(f"ЩИТ: {int(self.player.shield)}", True, GameConfig.WHITE)
        self.screen.blit(sh_txt, (28, 36))

        # Счёт, кристаллы, сектор и комбо
        score_s = self.font_md.render(f"ОЧКИ: {self.score}", True, GameConfig.NEON_YELLOW)
        cryst_s = self.font_md.render(f"КРИСТАЛЛЫ: {self.save_mgr.data['crystals']}", True, GameConfig.CYAN)
        wave_s = self.font_md.render(f"СЕКТОР: {self.wave} ({self.wave_kills}/{self.wave_target_kills})", True, GameConfig.NEON_GREEN)
        combo_s = self.font_md.render(f"КОМБО: x{self.combo}", True, GameConfig.NEON_PINK)

        self.screen.blit(score_s, (275, 18))
        self.screen.blit(cryst_s, (515, 18))
        self.screen.blit(wave_s, (815, 18))
        self.screen.blit(combo_s, (1110, 18))

        # Полоска Босса, если Босс на экране
        for e in self.enemies:
            if e.is_boss:
                bw = 540
                bx = GameConfig.WIDTH // 2 - bw // 2
                by = 78
                bpct = max(0.0, e.hp / e.max_hp)
                pygame.draw.rect(self.screen, (30, 10, 30), (bx, by, bw, 24), border_radius=6)
                pygame.draw.rect(self.screen, GameConfig.NEON_RED, (bx, by, int(bw * bpct), 24), border_radius=6)
                pygame.draw.rect(self.screen, GameConfig.WHITE, (bx, by, bw, 24), 2, border_radius=6)
                b_txt = self.font_xs.render(f"{e.name}: {int(e.hp)} HP", True, GameConfig.WHITE)
                self.screen.blit(b_txt, (GameConfig.WIDTH // 2 - b_txt.get_width() // 2, by + 3))

        # Подсказка внизу
        hint = self.font_xs.render("[WASD / Стрелки] Полёт   |   [Q] Вызвать Щит Знаний (+Бонус)   |   [ESC] В Меню Ангара", True, GameConfig.GRAY)
        self.screen.blit(hint, (GameConfig.WIDTH // 2 - hint.get_width() // 2, GameConfig.HEIGHT - 24))

    # --------------------------------------------------------------------------
    # ОБРАЗОВАТЕЛЬНЫЙ МОДУЛЬ «ЩИТ ЗНАНИЙ» (EDU-QUIZ)
    # --------------------------------------------------------------------------
    def draw_edu_quiz(self):
        self.starfield.draw(self.screen)

        card = pygame.Rect(190, 110, 900, 500)
        pygame.draw.rect(self.screen, (18, 24, 52), card, border_radius=18)
        pygame.draw.rect(self.screen, GameConfig.NEON_PURPLE, card, 4, border_radius=18)

        cat_t = self.font_md.render(f"ЩИТ ЗНАНИЙ // {self.active_quiz['category']}", True, GameConfig.NEON_YELLOW)
        self.screen.blit(cat_t, (GameConfig.WIDTH // 2 - cat_t.get_width() // 2, 138))

        rew_t = self.font_sm.render(f"Награда за правильный ответ: {self.active_quiz['reward_desc']}", True, GameConfig.NEON_GREEN)
        self.screen.blit(rew_t, (GameConfig.WIDTH // 2 - rew_t.get_width() // 2, 178))

        # Отрисовка текста вопроса с переносом строк
        words = self.active_quiz["q"].split(" ")
        lines, cur = [], ""
        for w in words:
            if len(cur + " " + w) < 52:
                cur = (cur + " " + w).strip()
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)

        for idx, ln in enumerate(lines):
            q_surf = self.font_md.render(ln, True, GameConfig.WHITE)
            self.screen.blit(q_surf, (GameConfig.WIDTH // 2 - q_surf.get_width() // 2, 235 + idx * 34))

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.quiz_buttons:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen, self.font_sm)

        if self.quiz_feedback_text:
            col = GameConfig.NEON_GREEN if "ВЕРНО" in self.quiz_feedback_text else GameConfig.NEON_RED
            fb = self.font_md.render(self.quiz_feedback_text, True, col)
            self.screen.blit(fb, (GameConfig.WIDTH // 2 - fb.get_width() // 2, 540))

    def handle_quiz_answer(self, chosen_idx):
        if self.quiz_feedback_timer > 0:
            return
        if chosen_idx == self.active_quiz["correct"]:
            self.sound.play("powerup")
            self.quiz_feedback_text = "ВЕРНО! +120 КРИСТАЛЛОВ, РЕМОНТ И СУПЕР-ОРУЖИЕ АКТИВИРОВАНЫ!"
            self.save_mgr.data["crystals"] += 120
            self.save_mgr.data["quizzes_solved"] += 1
            if self.save_mgr.data["quizzes_solved"] >= 5:
                self.unlock_achievement("scholar_cat")
            self.save_mgr.save()

            self.player.hp = self.player.max_hp
            self.player.shield = self.player.max_shield
            self.player.overdrive_timer = 420
        else:
            self.sound.play("wrong")
            right_str = self.active_quiz["answers"][self.active_quiz["correct"]]
            self.quiz_feedback_text = f"ПОЧТИ! Правильный ответ: {right_str} (+25 кристаллов за старание)"
            self.save_mgr.data["crystals"] += 25
            self.save_mgr.save()

        self.quiz_feedback_timer = 75

    # --------------------------------------------------------------------------
    # АНГАР ПРОКАЧКИ И МАГАЗИН СКИНОВ
    # --------------------------------------------------------------------------
    def draw_hangar(self):
        self.starfield.update(0.4)
        self.starfield.draw(self.screen)

        mouse_pos = pygame.mouse.get_pos()
        self.btn_back_menu.check_hover(mouse_pos)
        self.btn_back_menu.draw(self.screen, self.font_sm)

        title = self.font_lg.render("КОСМИЧЕСКИЙ АНГАР И МАГАЗИН", True, GameConfig.NEON_YELLOW)
        self.screen.blit(title, (310, 28))

        cryst = self.font_md.render(f"БАЛАНС КРИСТАЛЛОВ: {self.save_mgr.data['crystals']}", True, GameConfig.CYAN)
        self.screen.blit(cryst, (910, 36))

        # Левая колонка: Прокачка систем корабля
        pygame.draw.rect(self.screen, (16, 22, 46), (40, 105, 640, 560), border_radius=14)
        pygame.draw.rect(self.screen, GameConfig.CYAN, (40, 105, 640, 560), 2, border_radius=14)
        sub1 = self.font_md.render("МОДЕРНИЗАЦИЯ СИСТЕМ КОРАБЛЯ", True, GameConfig.NEON_GREEN)
        self.screen.blit(sub1, (65, 122))

        labels = {
            "hull_level": ("Броня и Генератор Щита", "+35 Здоровья и +20 Щита"),
            "weapon_level": ("Лазерные Батареи", "+Урон и дополнительные стволы"),
            "speed_level": ("Турбо-Двигатели", "+Скорость и манёвренность"),
            "magnet_level": ("Грави-Магнит Лута", "+Радиус притяжения кристаллов"),
            "pet_drone_level": ("Боевой Кибер-Котик Дрон", "Автоматически стреляет ракетами")
        }

        for idx, (k, (name, desc)) in enumerate(labels.items()):
            y = 175 + idx * 82
            lvl = self.save_mgr.data["upgrades"][k]
            cost = 100 + lvl * 110
            maxed = lvl >= 5

            t1 = self.font_sm.render(f"{name} [Ур. {lvl}/5]", True, GameConfig.WHITE)
            t2 = self.font_xs.render(desc, True, GameConfig.GRAY)
            self.screen.blit(t1, (65, y + 2))
            self.screen.blit(t2, (65, y + 26))

            btn = self.upgrade_buttons[k]
            btn.text = "МАКС. УР." if maxed else f"УЛУЧШИТЬ ({cost})"
            btn.color = GameConfig.GRAY if maxed else GameConfig.NEON_GREEN
            btn.check_hover(mouse_pos)
            btn.draw(self.screen, self.font_xs)

        # Правая колонка: Скины Котиков-Пилотов
        pygame.draw.rect(self.screen, (16, 22, 46), (710, 105, 530, 560), border_radius=14)
        pygame.draw.rect(self.screen, GameConfig.GOLD, (710, 105, 530, 560), 2, border_radius=14)
        sub2 = self.font_md.render("КОЛЛЕКЦИЯ КОСМО-КОТОВ", True, GameConfig.GOLD)
        self.screen.blit(sub2, (735, 122))

        for i, skin in enumerate(SaveManager.SKINS_CATALOG):
            y = 175 + i * 115
            unlocked = skin["id"] in self.save_mgr.data["unlocked_skins"]
            selected = self.save_mgr.data["selected_skin"] == skin["id"]

            pygame.draw.circle(self.screen, skin["primary"], (755, y + 24), 22)
            pygame.draw.circle(self.screen, skin["ear_color"], (755, y + 24), 11)

            st_name = self.font_sm.render(skin["name"], True, skin["primary"])
            st_desc = self.font_xs.render(skin["bonus_text"], True, GameConfig.WHITE)
            self.screen.blit(st_name, (790, y + 2))
            self.screen.blit(st_desc, (790, y + 26))

            btn = self.skin_buttons[i]
            if selected:
                btn.text = "АКТИВЕН"
                btn.color = GameConfig.CYAN
            elif unlocked:
                btn.text = "ВЫБРАТЬ"
                btn.color = GameConfig.NEON_GREEN
            else:
                btn.text = f"КУПИТЬ ({skin['price']})"
                btn.color = GameConfig.GOLD

            btn.check_hover(mouse_pos)
            btn.draw(self.screen, self.font_xs)

    # --------------------------------------------------------------------------
    # ГЛАВНОЕ МЕНЮ И ЭКРАН ИТОГОВ МИССИИ
    # --------------------------------------------------------------------------
    def draw_menu(self):
        self.starfield.update(0.7)
        self.starfield.draw(self.screen)

        cx = GameConfig.WIDTH // 2
        title1 = self.font_xl.render("STAR PAWS: КОТО-ПАТРУЛЬ", True, GameConfig.CYAN)
        title2 = self.font_md.render("КОСМИЧЕСКАЯ АРКАДА + ТРЕНАЖЁР ЗНАНИЙ (MVP EDITION)", True, GameConfig.NEON_YELLOW)
        self.screen.blit(title1, (cx - title1.get_width() // 2, 95))
        self.screen.blit(title2, (cx - title2.get_width() // 2, 162))

        # Статистика пилота
        stats_str = (
            f"Рекорд очков: {self.save_mgr.data['high_score']}   |   "
            f"Кристаллы: {self.save_mgr.data['crystals']}   |   "
            f"Решено задач: {self.save_mgr.data['quizzes_solved']}   |   "
            f"Открыто достижений: {sum(1 for v in self.save_mgr.data['achievements'].values() if v)}/5"
        )
        st_surf = self.font_sm.render(stats_str, True, GameConfig.NEON_GREEN)
        self.screen.blit(st_surf, (cx - st_surf.get_width() // 2, 220))

        mouse_pos = pygame.mouse.get_pos()
        for b in (self.btn_play, self.btn_hangar, self.btn_quiz_train, self.btn_quit):
            b.check_hover(mouse_pos)
            b.draw(self.screen, self.font_sm)

        # Список достижений внизу главного меню
        ach_y = 615
        ach_title = self.font_xs.render("ЗАЛ СЛАВЫ ПИЛОТА (ДОСТИЖЕНИЯ):", True, GameConfig.GOLD)
        self.screen.blit(ach_title, (60, ach_y))
        idx = 0
        for key, (name, _) in SaveManager.ACHIEVEMENTS_INFO.items():
            done = self.save_mgr.data["achievements"].get(key, False)
            col = GameConfig.NEON_GREEN if done else GameConfig.GRAY
            mark = "[✓]" if done else "[ ]"
            txt = self.font_xs.render(f"{mark} {name}", True, col)
            self.screen.blit(txt, (60 + idx * 235, ach_y + 26))
            idx += 1

    def draw_game_over(self):
        self.starfield.update(0.3)
        self.starfield.draw(self.screen)

        cx = GameConfig.WIDTH // 2
        card = pygame.Rect(cx - 320, 140, 640, 430)
        pygame.draw.rect(self.screen, (20, 18, 42), card, border_radius=18)
        pygame.draw.rect(self.screen, GameConfig.NEON_RED, card, 3, border_radius=18)

        t1 = self.font_lg.render("МИССИЯ ЗАВЕРШЕНА!", True, GameConfig.NEON_YELLOW)
        t2 = self.font_md.render(f"Набрано очков: {self.score}", True, GameConfig.WHITE)
        t3 = self.font_md.render(f"Добыто кристаллов за вылет: +{self.session_crystals}", True, GameConfig.CYAN)
        t4 = self.font_sm.render(f"Пройдено секторов: {self.wave}", True, GameConfig.NEON_GREEN)
        t5 = self.font_sm.render("Нажми [SPACE] для нового вылета или [ESC] для входа в Ангар", True, GameConfig.GOLD)

        self.screen.blit(t1, (cx - t1.get_width() // 2, 185))
        self.screen.blit(t2, (cx - t2.get_width() // 2, 265))
        self.screen.blit(t3, (cx - t3.get_width() // 2, 315))
        self.screen.blit(t4, (cx - t4.get_width() // 2, 365))
        self.screen.blit(t5, (cx - t5.get_width() // 2, 470))

    # --------------------------------------------------------------------------
    # ГЛАВНЫЙ ЦИКЛ ПРИЛОЖЕНИЯ
    # --------------------------------------------------------------------------
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_mgr.save()
                    running = False

                if self.state == "MENU":
                    if self.btn_play.is_clicked(event):
                        self.sound.play("powerup")
                        self.reset_combat_session()
                        self.state = "PLAYING"
                    elif self.btn_hangar.is_clicked(event):
                        self.sound.play("coin")
                        self.state = "HANGAR"
                    elif self.btn_quiz_train.is_clicked(event):
                        self.sound.play("powerup")
                        self.start_edu_quiz(from_menu=True)
                    elif self.btn_quit.is_clicked(event):
                        self.save_mgr.save()
                        running = False

                elif self.state == "HANGAR":
                    if self.btn_back_menu.is_clicked(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        self.state = "MENU"

                    for k, btn in self.upgrade_buttons.items():
                        if btn.is_clicked(event):
                            lvl = self.save_mgr.data["upgrades"][k]
                            cost = 100 + lvl * 110
                            if lvl < 5 and self.save_mgr.data["crystals"] >= cost:
                                self.save_mgr.data["crystals"] -= cost
                                self.save_mgr.data["upgrades"][k] += 1
                                self.save_mgr.save()
                                self.sound.play("powerup")
                            else:
                                self.sound.play("wrong")

                    for i, btn in enumerate(self.skin_buttons):
                        if btn.is_clicked(event):
                            skin = SaveManager.SKINS_CATALOG[i]
                            if skin["id"] in self.save_mgr.data["unlocked_skins"]:
                                self.save_mgr.data["selected_skin"] = skin["id"]
                                self.save_mgr.save()
                                self.sound.play("coin")
                            elif self.save_mgr.data["crystals"] >= skin["price"]:
                                self.save_mgr.data["crystals"] -= skin["price"]
                                self.save_mgr.data["unlocked_skins"].append(skin["id"])
                                self.save_mgr.data["selected_skin"] = skin["id"]
                                self.save_mgr.save()
                                self.sound.play("powerup")
                            else:
                                self.sound.play("wrong")

                elif self.state == "PLAYING":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.save_mgr.save()
                            self.state = "MENU"
                        elif event.key == pygame.K_q:
                            self.start_edu_quiz(from_menu=False)

                elif self.state == "EDU_QUIZ":
                    for i, btn in enumerate(self.quiz_buttons):
                        if btn.is_clicked(event):
                            self.handle_quiz_answer(i)
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                            idx = event.key - pygame.K_1
                            self.handle_quiz_answer(idx)

                elif self.state == "GAME_OVER":
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            self.reset_combat_session()
                            self.state = "PLAYING"
                        elif event.key == pygame.K_ESCAPE:
                            self.state = "HANGAR"

            # Отрисовка и логика текущего состояния
            if self.state == "MENU":
                self.draw_menu()
            elif self.state == "HANGAR":
                self.draw_hangar()
            elif self.state == "PLAYING":
                self.update_playing()
                self.draw_playing()
            elif self.state == "EDU_QUIZ":
                self.draw_edu_quiz()
                if self.quiz_feedback_timer > 0:
                    self.quiz_feedback_timer -= 1
                    if self.quiz_feedback_timer == 0:
                        self.state = "MENU" if self.quiz_from_menu else "PLAYING"
            elif self.state == "GAME_OVER":
                self.draw_game_over()

            # Всплывающий баннер достижения поверх экрана
            if self.achievement_timer > 0 and self.achievement_banner:
                self.achievement_timer -= 1
                banner_rect = pygame.Rect(GameConfig.WIDTH // 2 - 340, 72, 680, 44)
                pygame.draw.rect(self.screen, (20, 45, 30), banner_rect, border_radius=10)
                pygame.draw.rect(self.screen, GameConfig.GOLD, banner_rect, 2, border_radius=10)
                b_txt = self.font_sm.render(self.achievement_banner, True, GameConfig.GOLD)
                self.screen.blit(b_txt, (GameConfig.WIDTH // 2 - b_txt.get_width() // 2, 83))

            pygame.display.flip()
            self.clock.tick(GameConfig.FPS)

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = StarPawsGame()
    game.run()