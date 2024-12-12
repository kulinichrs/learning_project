import datetime
import inspect
import cv2 as cv
import numpy as np
from threading import Thread, Lock
import time
import config as cfg
from collections import deque


def is_in_dynamic_range(color, target, delta=25):
    lower = [max(0, target[i] - delta) for i in range(3)]
    upper = [min(255, target[i] + delta) for i in range(3)]
    return all(lower[i] <= color[i] <= upper[i] for i in range(3))


class Detection:
    def __init__(self, renderer=None):
        self.stopped = False
        self.enough_hp = True
        self.target_full_hp = True
        self.enough_mana = False
        self.skill_is_pressed = False

        self.TARGET_MAX_HP_color = ""
        self.lock = Lock()
        self.screenshot = None
        self.mobs_coordinates = []
        self.have_target = False
        self.have_buffs = False
        self.have_animus = False
        self.atk_pressed = False
        self.MYHP_DOT_color = ""
        self.MYMP_DOT_color = ""
        self.ANIMUS_HP_DOT_color = ""
        self.ANIMUS_EXIT_DOT_color = ""
        self.SKILL_DOT_color = ""
        self.TARGET_DOT1_color = ""
        self.TARGET_DOT2_color = ""
        self.rebuff_time = datetime.datetime.now()
        self.animus_attempt_time = datetime.datetime.now()
        self.renderer = renderer
        self.frame_delay = cfg.LOAD_LIMIT_FRAMETIME

        # История изменений для параметров (буфер из 3 значений)
        self.history_len = 3

        self.hist_have_target = deque(maxlen=self.history_len)
        self.hist_target_full_hp = deque(maxlen=self.history_len)
        self.hist_have_animus = deque(maxlen=self.history_len)
        self.hist_skill_is_pressed = deque(maxlen=self.history_len)
        self.hist_enough_mana = deque(maxlen=self.history_len)
        self.hist_enough_hp = deque(maxlen=self.history_len)
        self.hist_mobs_coordinates = deque(maxlen=self.history_len)

        # Добавляем элементы для отладки в рендерер
        for area in [
            cfg.SKILL_PANEL_AREA,
            cfg.HP_BAR_AREA,
            cfg.CHAT_AREA,
            cfg.BUFFS_AREA,
            cfg.RADAR_AREA,
            cfg.TOP_AREA,
            cfg.BOTTOM_AREA
        ]:
            self.renderer.add_element(
                f"{area}",
                "rectangle",
                {
                    "start": (area[0][0], area[0][1]),
                    "end": (area[1][0], area[1][1]),
                    "color": (0, 0, 255),
                    "thickness": 1,
                },
            )

        for dot in [
            cfg.MYHP_DOT,
            cfg.MYMP_DOT,
            cfg.ANIMUS_HP_DOT,
            cfg.ANIMUS_EXIT_DOT,
            cfg.SKILL_DOT,
            cfg.TARGET_DOT1,
            cfg.TARGET_DOT2,
            cfg.TARGET_MAX_HP_DOT
        ]:
            self.renderer.add_element(
                f"{dot}",
                "circle",
                {
                    "center": (dot[0], dot[1]),
                    "radius": 5,
                    "color": (255, 255, 0),
                    "thickness": 1,
                },
            )

    def update(self, screenshot):
        with self.lock:
            self.screenshot = screenshot

    def get_char_data(self):
        return [
            self.have_target,
            self.target_full_hp,
            self.have_animus,
            self.mobs_coordinates,
            self.skill_is_pressed,
            self.enough_mana,
            self.enough_hp,
        ]

    def get_dot_data(self):
        return [
            self.MYHP_DOT_color,
            self.MYMP_DOT_color,
            self.ANIMUS_HP_DOT_color,
            self.ANIMUS_EXIT_DOT_color,
            self.SKILL_DOT_color,
            self.TARGET_DOT1_color,
            self.TARGET_DOT2_color,
            self.TARGET_MAX_HP_color
        ]

    def update_dot_color_inf(self, screenshot):
        try:
            if len(screenshot.shape) == 3 and screenshot.shape[2] == 3:
                self.MYHP_DOT_color = self.get_RGB_color(screenshot, cfg.MYHP_DOT)
                self.MYMP_DOT_color = self.get_RGB_color(screenshot, cfg.MYMP_DOT)
                self.ANIMUS_HP_DOT_color = self.get_RGB_color(screenshot, cfg.ANIMUS_HP_DOT)
                self.ANIMUS_EXIT_DOT_color = self.get_RGB_color(screenshot, cfg.ANIMUS_EXIT_DOT)
                self.SKILL_DOT_color = self.get_RGB_color(screenshot, cfg.SKILL_DOT)
                self.TARGET_DOT1_color = self.get_RGB_color(screenshot, cfg.TARGET_DOT1)
                self.TARGET_DOT2_color = self.get_RGB_color(screenshot, cfg.TARGET_DOT2)
                self.TARGET_MAX_HP_color = self.get_RGB_color(screenshot, cfg.TARGET_MAX_HP_DOT)
            elif len(screenshot.shape) == 3 and screenshot.shape[2] == 4:
                rgb_image = screenshot[..., :3]
                self.MYHP_DOT_color = self.get_RGB_color(rgb_image, cfg.MYHP_DOT)
                self.MYMP_DOT_color = self.get_RGB_color(rgb_image, cfg.MYMP_DOT)
                self.ANIMUS_HP_DOT_color = self.get_RGB_color(rgb_image, cfg.ANIMUS_HP_DOT)
                self.ANIMUS_EXIT_DOT_color = self.get_RGB_color(rgb_image, cfg.ANIMUS_EXIT_DOT)
                self.SKILL_DOT_color = self.get_RGB_color(rgb_image, cfg.SKILL_DOT)
                self.TARGET_DOT1_color = self.get_RGB_color(rgb_image, cfg.TARGET_DOT1)
                self.TARGET_DOT2_color = self.get_RGB_color(rgb_image, cfg.TARGET_DOT2)
                self.TARGET_MAX_HP_color = self.get_RGB_color(rgb_image, cfg.TARGET_MAX_HP_DOT)
            else:
                print("Warning: Screenshot does not have 3 or 4 channels, skipping color extraction.")
        except Exception as e:
            print(f"Error in update_dot_color_inf: {e}")

    def get_RGB_color(self, screenshot, dot_coordinates):
        x, y = dot_coordinates
        bgr_color = screenshot[y, x].tolist()
        return bgr_color

    def start(self):
        self.stopped = False
        print(f"Detection(id={self}) starting ")
        Thread(target=self.run, daemon=True).start()

    def stop(self):
        print(f"Detection(id={self}) stopping ")
        self.stopped = True

    def run(self):
        while not self.stopped:
            start_time = time.time()

            if self.screenshot is None:
                time.sleep(self.frame_delay)
                continue

            with self.lock:
                # Создаем локальные копии, если нужно
                pass

            self.process_frame()

            elapsed_time = time.time() - start_time
            sleep_time = max(0, self.frame_delay - elapsed_time)
            time.sleep(sleep_time)

    def process_frame(self):
        with self.lock:
            screenshot = self.screenshot.copy()

        self.update_dot_color_inf(screenshot)

        # Фильтрация по желтому цвету (мобы)
        lower_yellow = np.array(cfg.COLOR_YELLOW_LOWER)
        upper_yellow = np.array(cfg.COLOR_YELLOW_UPPER)
        mask = cv.inRange(screenshot, lower_yellow, upper_yellow)

        # Исключаем области интерфейса
        for area in [
            cfg.SKILL_PANEL_AREA,
            cfg.HP_BAR_AREA,
            cfg.CHAT_AREA,
            cfg.BUFFS_AREA,
            cfg.RADAR_AREA,
            cfg.TOP_AREA,
            cfg.BOTTOM_AREA
        ]:
            mask = self.filter_mask(mask, area)

        min_area = 6
        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        filtered_contours = [cnt for cnt in contours if cv.contourArea(cnt) > min_area]

        mobs_coords_local = []
        for contour in filtered_contours:
            x, y, w, h = cv.boundingRect(contour)
            mobs_coords_local.append([x + w // 2, y + h // 2])

        _have_target = is_in_dynamic_range(self.TARGET_DOT1_color, cfg.TARGET_DOT1_COLOR, delta=55) and \
            is_in_dynamic_range(self.TARGET_DOT2_color, cfg.TARGET_DOT2_COLOR, delta = 55)
        _target_full_hp = is_in_dynamic_range(self.TARGET_MAX_HP_color, cfg.TARGET_MAX_HP_DOT_COLOR)
        _have_animus = is_in_dynamic_range(self.ANIMUS_HP_DOT_color, cfg.ANIMUS_HP_DOT_COLOR) and \
            is_in_dynamic_range(self.ANIMUS_EXIT_DOT_color, cfg.ANIMUS_EXIT_DOT_COLOR)
        _skill_is_pressed = not is_in_dynamic_range(self.SKILL_DOT_color, cfg.SKILL_DOT_COLOR, 10)
        _enough_mana = is_in_dynamic_range(self.MYMP_DOT_color, cfg.MYMP_DOT_COLOR)
        _enough_hp = is_in_dynamic_range(self.MYHP_DOT_color, cfg.MYHP_DOT_COLOR)

        # Добавляем значения в историю
        self.hist_have_target.append(_have_target)
        self.hist_target_full_hp.append(_target_full_hp)
        self.hist_have_animus.append(_have_animus)
        self.hist_skill_is_pressed.append(_skill_is_pressed)
        self.hist_enough_mana.append(_enough_mana)
        self.hist_enough_hp.append(_enough_hp)
        self.hist_mobs_coordinates.append(mobs_coords_local)

        # Проверяем стабилизацию значений (пример: все три последних значения должны совпадать)
        if len(self.hist_have_target) == self.history_len and len(set(self.hist_have_target)) == 1:
            final_have_target = self.hist_have_target[0]
        else:
            final_have_target = self.have_target  # Сохраняем старое значение

        if len(self.hist_target_full_hp) == self.history_len and len(set(self.hist_target_full_hp)) == 1:
            final_target_full_hp = self.hist_target_full_hp[0]
        else:
            final_target_full_hp = self.target_full_hp

        if len(self.hist_have_animus) == self.history_len and len(set(self.hist_have_animus)) == 1:
            final_have_animus = self.hist_have_animus[0]
        else:
            final_have_animus = self.have_animus

        if len(self.hist_skill_is_pressed) == self.history_len and len(set(self.hist_skill_is_pressed)) == 1:
            final_skill_is_pressed = self.hist_skill_is_pressed[0]
        else:
            final_skill_is_pressed = self.skill_is_pressed

        if len(self.hist_enough_mana) == self.history_len and len(set(self.hist_enough_mana)) == 1:
            final_enough_mana = self.hist_enough_mana[0]
        else:
            final_enough_mana = self.enough_mana

        if len(self.hist_enough_hp) == self.history_len and len(set(self.hist_enough_hp)) == 1:
            final_enough_hp = self.hist_enough_hp[0]
        else:
            final_enough_hp = self.enough_hp

        # Для мобов можно решить, как считать "стабильность".
        # Если хотим, чтобы координаты менялись только если трижды подряд одно и то же (что маловероятно),
        # можно упрощенно сказать: если хоть один кадр отличается, меняем сразу.
        # Для упрощения предположим: если трижды подряд одинаковый набор координат (это маловероятно),
        # тогда обновляем. Иначе оставляем старый.
        # Но для мобов, возможно, лучше обновлять сразу или с другим критерием.
        if len(self.hist_mobs_coordinates) == self.history_len and all(self.hist_mobs_coordinates[0] == c for c in self.hist_mobs_coordinates):
            final_mobs_coordinates = self.hist_mobs_coordinates[0]
        else:
            # Можно либо взять последнее, либо оставить старое:
            final_mobs_coordinates = mobs_coords_local  # Или self.mobs_coordinates

        with self.lock:
            self.have_target = final_have_target
            self.target_full_hp = final_target_full_hp
            self.have_animus = final_have_animus
            self.mobs_coordinates = final_mobs_coordinates
            self.skill_is_pressed = final_skill_is_pressed
            self.enough_mana = final_enough_mana
            self.enough_hp = final_enough_hp

        if self.renderer:
            self.visualize_debug_info(mask, final_mobs_coordinates)

    def filter_mask(self, mask_to_filter, filter_range):
        mask_to_filter[filter_range[0][1]:filter_range[1][1],
                       filter_range[0][0]:filter_range[1][0]] = 0
        return mask_to_filter

    def visualize_debug_info(self, mask, mobs_coordinates):
        self.renderer.remove_mob_elements()
        for i, (x, y) in enumerate(mobs_coordinates):
            self.renderer.add_element(
                f"mob_{i}",
                "circle",
                {
                    "center": (x, y),
                    "radius": 10,
                    "color": (0, 255, 0),
                    "thickness": 2,
                },
                mob=True
            )
            self.renderer.add_element(
                f"mob_text_{i}",
                "text",
                {
                    "text": f"Mob {i}",
                    "position": (x + 15, y + 15),
                    "color": (255, 255, 255),
                    "font_scale": 0.5,
                    "thickness": 1,
                },
                mob=True
            )
