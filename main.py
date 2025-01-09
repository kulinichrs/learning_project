import os
import time
from time import sleep

import numpy as np

import config as cfg
from lib.bot import RFBot
import cv2 as cv
from lib.detection import Detection
from lib.windowcapture import WindowCapture
from lib.screen_render import ScreenRenderer

# Перемещаем рабочую директорию в путь скрипта
os.chdir(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True  # Флаг для включения/выключения режима отладки


def initialize_objects():
    """
    Инициализация всех необходимых объектов.
    """
    wincap = WindowCapture("157712709@win-sjen2colrir - Remote Desktop - RustDesk")

    renderer = ScreenRenderer(wincap = wincap)
    detector = Detection(renderer)
    bot = RFBot(renderer)
    return wincap, detector, bot, renderer


def draw_debug_info(renderer, detector, bot):
    """
    Добавляет отладочную информацию и объекты в `ScreenRenderer`.
    """
    # Получение данных от детектора и бота
    detection_state_text = ""
    try:
        _position = bot.mouse.position
        _RGBcolor = detector.get_RGB_color(detector.screenshot, _position)
        _HSVcolor = cv.cvtColor(np.uint8([[_RGBcolor]]), cv.COLOR_BGR2HSV)[0][0].tolist()
        detection_state_text = f"""
        rebuffT: {int(bot.rebuff_time-time.time())}
        mouse_position: {_position}
        mouse_color RGB: {_RGBcolor}
        mouse_color HSV: {_HSVcolor}
        BATTLE_mode: {bot.battle_mode}
        have_close_targets: {bot.have_close_targets_left}
        """
    except:
        pass

    bot_state_text = f""" 
    State: {bot.get_current_state()}
    target: {bot.have_target}
    target full HP: {bot.target_full_hp}
    animus: {bot.have_animus}
    skill_pressed: {bot.skill_is_pressed}
    stopped: {bot.stopped}
    kill_count: {bot.kill_counter}
    """
    dot_data = detector.get_dot_data()

    dot_state_text = f"""
    Dot state:
    MYHP: {dot_data[0]}
    MYMP: {dot_data[1]}
    ANIMUS_HP: {dot_data[2]}
    ANIMUS_EXIT: {dot_data[3]}
    SKILL_DOT: {dot_data[4]}
    TARGET_DOT1: {dot_data[5]}
    TARGET_DOT2: {dot_data[6]}
    TARGET_hp: {dot_data[7]}
    """


    # Добавление текстовой информации
    for i, line in enumerate(bot_state_text.split('\n')):
        renderer.add_element(
            f"bot_text_line_{i}",
            "text",
            {
                "text": line.strip(),
                "position": (30, 50 + i * 23),
                "color": (248, 248, 255),
                "font_scale": 0.6,
                "thickness": 1,
            },
        )
    for i, line in enumerate(detection_state_text.split('\n')):
        renderer.add_element(
            f"detection_text_line_{i}",
            "text",
            {
                "text": line.strip(),
                "position": (230, 50 + i * 23),
                "color": (248, 248, 255),
                "font_scale": 0.6,
                "thickness": 1,
            },
        )
    try:
        for i, line in enumerate(dot_state_text.split('\n')):
            renderer.add_element(
                f"dot_text_line_{i}",
                "text",
                {
                    "text": line.strip(),
                    "position": (580, 10 + i * 23),
                    "color":  dot_data[i-2] if i >= 2 else (248, 248, 255),
                    "font_scale": 0.8,
                    "thickness": 1,
                },
            )
    except IndexError:
        pass

def main_loop(wincap, detector, bot, renderer):
    """
    Главный цикл программы.
    """
    Active = True
    while Active:
        # Пропускаем итерацию, если скриншот недоступен
        if wincap.screenshot is None:
            continue

        # Обновляем данные детектора и бота
        detector.update(wincap.screenshot)
        bot.update_screenshot(wincap.screenshot)
        bot.update_char_data(detector.get_char_data())

        if DEBUG:

            # Добавляем новые элементы в отладочном режиме
            draw_debug_info(renderer, detector, bot)

        # Проверка нажатия клавиш
        key = cv.waitKey(cfg.KEY_WAIT_MS)
        if key == ord('q'):  # Завершение программы
            Active = False

        if bot.stopped or detector.stopped or renderer.stopped or wincap.stopped:
            Active = False

    bot.stop()
    detector.stop()
    renderer.stop()
    wincap.stop()


def main():
    """
    Основная точка входа в программу.
    """
    # Инициализация объектов
    wincap, detector, bot, renderer = initialize_objects()

    # Запуск потоков
    wincap.start()
    sleep(1)
    renderer.start()
    detector.start()
    bot.start()

    # Главный цикл
    try:
        main_loop(wincap, detector, bot, renderer)
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        print("Shutting down...")
        bot.stop()
        detector.stop()
        wincap.stop()
        renderer.stop()


if __name__ == "__main__":
    main()
