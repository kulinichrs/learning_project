from idlelib.configdialog import help_pages

import cv2 as cv
import numpy as np

from lib.screen_render import ScreenRenderer
from lib.windowcapture import WindowCapture
import config as cfg


class ConfigEditor:
    def __init__(self, window_name, config_path, renderer=None):
        """
        Инициализация редактора конфигурации.
        :param window_name: Название окна для захвата.
        :param config_path: Путь к файлу конфигурации.
        :param renderer: Экземпляр ScreenRenderer для визуализации.
        """
        self.wincap = WindowCapture(window_name)
        self.wincap.start()
        self.config_path = config_path
        self.selected_areas = []
        self.selected_color_ranges = []
        self.renderer = renderer  # Экземпляр ScreenRenderer для визуализации

    def select_area(self, frame):
        """
        Позволяет пользователю выделить прямоугольную область на текущем кадре.
        :param frame: Кадр из окна.
        """
        def draw_rectangle(event, x, y, flags, param):
            nonlocal start_x, start_y, drawing
            if event == cv.EVENT_LBUTTONDOWN:
                start_x, start_y = x, y
                drawing = True
            elif event == cv.EVENT_MOUSEMOVE and drawing:
                temp_frame = frame.copy()
                cv.rectangle(temp_frame, (start_x, start_y), (x, y), (0, 255, 0), 2)
                cv.imshow("Select Area", temp_frame)
            elif event == cv.EVENT_LBUTTONUP:
                drawing = False
                rel_start_x = start_x - self.wincap.offset_x
                rel_start_y = start_y - self.wincap.offset_y
                rel_end_x = x - self.wincap.offset_x
                rel_end_y = y - self.wincap.offset_y
                self.selected_areas.append((rel_start_x, rel_start_y, rel_end_x, rel_end_y))
                print(f"Selected area: {self.selected_areas[-1]}")

        drawing = False
        start_x, start_y = -1, -1

        cv.namedWindow("Select Area")
        cv.setMouseCallback("Select Area", draw_rectangle)

        while True:
            with self.wincap.lock:
                frame = self.wincap.screenshot.copy()

            cv.imshow("Select Area", frame)
            key = cv.waitKey(1) & 0xFF
            if key == ord("q"):
                break
        cv.destroyAllWindows()

    def select_color(self, frame):
        """
        Позволяет пользователю выбрать цвет пикселя и визуально оценить диапазон.
        :param frame: Кадр из окна.
        """
        def pick_color(event, x, y, flags, param):
            if event == cv.EVENT_LBUTTONDOWN:
                # Получаем цвет в формате BGR
                bgr_color = frame[y, x].tolist()
                # Конвертируем в HSV
                hsv_color = cv.cvtColor(np.uint8([[bgr_color]]), cv.COLOR_BGR2HSV)[0][0].tolist()
                lower_bound, upper_bound = self.calculate_color_range(hsv_color)
                self.selected_color_ranges.append((lower_bound, upper_bound))
                print(f"Selected color range (HSV): LOWER={lower_bound}, UPPER={upper_bound}")

                # Визуализируем через ScreenRenderer
                self.renderer.add_element(
                    f"color_{len(self.selected_color_ranges)}",
                    "circle",
                    {
                        "center": (x, y),
                        "radius": 10,
                        "color": (0, 255, 0),
                        "thickness": 2,
                    },
                )
                # Показ выделения объектов
                mask = cv.inRange(cv.cvtColor(frame, cv.COLOR_BGR2HSV), np.array(lower_bound), np.array(upper_bound))
                result = cv.bitwise_and(frame, frame, mask=mask)
                cv.imshow("Color Range Preview", result)

            # Отображаем координаты и цвет под курсором
            abs_pos = (x, y)
            rel_pos = (x - self.wincap.offset_x, y - self.wincap.offset_y)
            b, g, r = frame[y, x]

            # Отображаем эту информацию на экране
            display_text = f"Abs: ({abs_pos[0]}, {abs_pos[1]}) | Rel: ({rel_pos[0]}, {rel_pos[1]}) | Color: ({r}, {g}, {b})"
            self.renderer.add_element(
                "cursor_info",
                "text",
                {
                    "text": display_text,
                    "position": (frame.shape[1] - 350, 30),  # Позиция текста в правом верхнем углу
                    "color": (255, 255, 255),
                    "font_scale": 0.5,
                    "thickness": 1,
                },
            )

            # Графическая подсветка курсора
            self.renderer.add_element(
                f"cursor_highlight_{x}_{y}",
                "circle",
                {
                    "center": (x, y),
                    "radius": 15,  # Радиус подсветки
                    "color": (0, 255, 0),  # Зеленый
                    "thickness": 2,
                },
            )

        cv.namedWindow("Pick Color")
        cv.setMouseCallback("Pick Color", pick_color)

        while True:
            with self.wincap.lock:
                frame = self.wincap.screenshot.copy()

            cv.imshow("Pick Color", frame)
            key = cv.waitKey(1) & 0xFF
            if key == ord("q"):
                break
        cv.destroyAllWindows()

    @staticmethod
    def calculate_color_range(hsv_color):
        """
        Рассчитывает диапазон HSV цвета с отклонением ±5%.
        :param hsv_color: Цвет в формате HSV.
        :return: Нижняя и верхняя границы диапазона.
        """
        range_percent = 0.05  # 5% отклонения
        lower_bound = [
            max(0, int(hsv_color[0] * (1 - range_percent))),  # Hue
            max(0, int(hsv_color[1] * (1 - range_percent))),  # Saturation
            max(0, int(hsv_color[2] * (1 - range_percent))),  # Value
        ]
        upper_bound = [
            min(179, int(hsv_color[0] * (1 + range_percent))),  # Hue (макс. 179)
            min(255, int(hsv_color[1] * (1 + range_percent))),  # Saturation (макс. 255)
            min(255, int(hsv_color[2] * (1 + range_percent))),  # Value (макс. 255)
        ]
        return lower_bound, upper_bound

    def save_to_config(self):
        """
        Сохраняет выбранные области и диапазоны цветов в файл конфигурации.
        """
        with open(self.config_path, "a") as f:
            for area in self.selected_areas:
                if isinstance(area, tuple):
                    print(f"SELECTED_AREA = {str(list(area))}  # Относительно окна\n")
                    f.write(f"SELECTED_AREA = {str(list(area))}  # Относительно окна\n")
                else:
                    print(f"Skipping invalid area: {area}")
            for lower, upper in self.selected_color_ranges:
                if isinstance(lower, list) and isinstance(upper, list):
                    f.write(f"COLOR_RANGE = {{'LOWER': {lower}, 'UPPER': {upper}}}  # Диапазон HSV\n")
                else:
                    print(f"Skipping invalid color range: LOWER={lower}, UPPER={upper}")
        print("Configuration updated!")

    def stop(self):
        """
        Останавливает захват окна.
        """
        self.wincap.stop()


if __name__ == "__main__":
    # Название окна
    window_name = "157712709@win-sjen2colrir - Remote Desktop - RustDesk"

    # Путь к файлу конфигурации
    config_path = "config.py"
    wincap = WindowCapture(window_name)

    render  = ScreenRenderer(wincap = wincap)
    editor = ConfigEditor(window_name, config_path, render)

    try:
        print("Step 1: Select an area")
        with editor.wincap.lock:
            initial_frame = editor.wincap.get_screenshot().copy()
        editor.select_area(initial_frame)

        print("Step 2: Pick colors and confirm ranges")
        with editor.wincap.lock:
            initial_frame = editor.wincap.get_screenshot().copy()
        editor.select_color(initial_frame)

        print("Step 3: Save to configuration")
        editor.save_to_config()
    finally:
        editor.stop()


# target area (387, 264, 407, 288)
# targethp  (553, 271, 553, 271)
# animus (135, 290, 148, 302)
# buff  (930, 345, 971, 526)
# skill_panel (336, 773, 525, 831)
#
# mymp  (88, 257, 88, 257)
# myhp (75, 245, 75, 245)
#
# farmingarea (16, 324, 925, 678)

# LOWER=[26, 236, 152], UPPER=[29, 255, 168]