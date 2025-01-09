import time
import math
from pynput.mouse import Controller, Button
from pynput.keyboard import Controller as Keyboard, Key
from threading import Thread, Lock
from time import sleep
import config as cfg
from lib.botstatemanager import BotStateManager
from lib.states.states import *


class RFBot:
    def __init__(self, renderer=None):
        self.stopping = False
        self.lock = Lock()
        self.renderer = renderer
        self.mouse = Controller()
        self.keyboard = Keyboard()

        # Инициализация состояния через менеджер
        self.state_manager = BotStateManager(StartState())

        # Остальные атрибуты
        self.have_target = False
        self.have_animus = False
        self.target_full_hp = True
        self.skill_is_pressed = False
        self.enough_mana = True
        self.enough_hp = True
        self.battle_mode = False
        self.have_close_targets_left = False
        self.current_weapon =  'main'
        self.mobs = []
        self.screenshot = None
        self.prev_attack = False
        self.aggro_counter = 0
        self.kill_counter = 0
        self.stopped = True
        self.frame_delay = cfg.LOAD_LIMIT_FRAMETIME + 0.04
        self.stop_time = time.time() + cfg.BOT_RUNTIME_LIMIT_HOURS * 3600
        self.rebuff_time = time.time()
        self.potion_time = time.time()
        self.animus_last_see_time = time.time()
        self.mob_ignore_timeout = time.time()

    def get_current_state(self):
        if self.state_manager.current_state:
            return self.state_manager.current_state.__class__.__name__
        return "Unknown"

    def log(self, msg):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print(f"[{timestamp}] {msg}")

    def update_char_data(self, args):
        with self.lock:
            self.have_target = args[0]
            self.target_full_hp = args[1]
            self.have_animus = args[2]
            self.mobs = list(args[3])
            self.skill_is_pressed = args[4]
            self.enough_mana = args[5]
            self.enough_hp = args[6]
            self.battle_mode = args[7]
            self.have_close_targets_left = args[8]

    def update_screenshot(self, screenshot):
        with self.lock:
            self.screenshot = screenshot

    def start(self):
        self.stopped = False
        sleep(3)
        self.log(f"Bot start in {cfg.BOT_START_DELAY_HOURS} hours")
        sleep(60 * cfg.BOT_START_DELAY_HOURS)
        self.log("Bot Started")
        Thread(target=self.run, daemon=True).start()

    def stop(self):
        self.stopped = True
        self.log("Бот остановлен")

    def run(self):
        while not self.stopped and not cfg.DETECTION_DEBUG_MODE:
            start_time = time.time()

            if time.time() > self.stop_time:
                self.log("Время работы истекло, останавливаем бота")
                self.stopping = True
                break

            try:
                self.state_manager.handle(self)
            except Exception as e:
                self.log(f"Ошибка в состоянии: {e}. Сбрасываем в BuffingState.")
                self.state_manager.set_state(BuffingState())

            elapsed_time = time.time() - start_time
            sleep_time = max(0, self.frame_delay - elapsed_time)
            time.sleep(sleep_time)

    def rotate(self, time_to_rotate="Short"):
        self.keyboard.press(Key.left)
        sleep(0.25 if time_to_rotate == "Short" else 0.4)
        self.keyboard.release(Key.left)
        sleep(2)

    def rebuff(self):
        if cfg.USE_POTIONS and self.potion_time < time.time():
            self.keyboard.press(Key.f7)
            self.keyboard.release(Key.f7)
            sleep(0.5)
            self.potion_time = time.time() + 300

        if self.rebuff_time < time.time():
            self.log("Накладываем баффы (F5)")
            self.keyboard.press(Key.f5)
            self.keyboard.release(Key.f5)
            sleep(2)
            while self.skill_is_pressed:
                sleep(1)
            self.rebuff_time = time.time() + cfg.REBUFF_TIMEOUT_SECODS

    def summon_animus(self):
        if not self.have_animus and self.animus_last_see_time < time.time():
            self.log("Призываем анимус (F6)")
            self.keyboard.press(Key.f6)
            sleep(0.1)
            self.keyboard.release(Key.f6)
            sleep(1)
            self.have_animus = True

    def select_target_by_coordinates(self, position):
        x, y = position
        self.mouse.position = (x, y)
        self.mouse.press(Button.left)
        sleep(0.1)
        self.mouse.release(Button.left)
        sleep(1)

    def select_target(self):
        if self.screenshot is None:
            self.log("Скриншот отсутствует, не можем выбрать цель.")
            return False
        if len(self.mobs) == 0:
            self.log("Список мобов пуст, некого выбирать.")
            return False

        retry_select_count = 0
        while not self.have_target and retry_select_count <= 5:

            self.mobs.sort(key=lambda mob: mob.distance_to_character, reverse=True)
            x, y = self.mobs[0].get_center()

            # Проверка границ
            h, w = self.screenshot.shape[:2]
            if not (0 <= y < h and 0 <= x < w):
                 return False

            if retry_select_count > 0:
                self.keyboard.press('v')
                sleep(0.01)
                self.keyboard.release('v')
                sleep(0.01)
                self.keyboard.press('q')
                sleep(0.01)
                self.keyboard.release('q')
                self.mouse.position = (x, y)
                if self.renderer:
                    self.renderer.add_element(
                        "Click",
                        "circle",
                        {"center": (x, y), "radius": 2, "color": (255, 255, 255), "thickness": 2},
                    )
                self.keyboard.press(Key.esc)
                sleep(0.01)
                self.keyboard.release(Key.esc)
                sleep(0.01)
                self.mouse.press(Button.left)
                self.mouse.release(Button.left)
                self.mob_ignore_timeout = time.time() + cfg.MOB_IGNORE_TIMEOUT_SECONDS
                sleep(1)

            retry_select_count += 1
        return self.have_target

    def attack_target(self):
        if self.mob_ignore_timeout < time.time() and self.target_full_hp:
            self.log("Цель не умирает. Сбрасываем.")
            self.keyboard.press(Key.esc)
            self.keyboard.release(Key.esc)
            sleep(1)
            return

        if self.have_target:
            if cfg.BOT_ANIMUS_CAREFUL and  self.have_animus and self.target_full_hp:
                self.log("Цель полна HP. Спамим клавиши (space + ',') для атаки анимусом.")
                # Спамим клавиши, пока цель full_hp и не истечет время игнорирования
                while self.have_target and self.target_full_hp and self.mob_ignore_timeout > time.time():
                    self.keyboard.press(',')
                    self.keyboard.release(',')
                    sleep(0.1)  # Небольшая пауза между нажатиями
                    self.keyboard.press(Key.space)
                    self.keyboard.release(Key.space)
                    sleep(0.1)  # Пауза между комбо-нажатием

            if not self.skill_is_pressed:
                self.keyboard.press(Key.f4)
                self.keyboard.release(Key.f4)
                self.skill_is_pressed = True
                sleep(1)

    def loot_mobs(self):
        self.kill_counter += 1
        self.log(f"Лутаем. Убито мобов: {self.kill_counter}")
        for _ in range(cfg.BOT_LOOT_TIME):
            self.keyboard.press("x")
            sleep(0.03)
            self.keyboard.release("x")
            sleep(0.01)
