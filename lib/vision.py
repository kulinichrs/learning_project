import cv2 as cv
import numpy as np
import config as cfg


class Vision:
    """
    Класс для обработки изображений:
    - Генерация точек клика.
    - Отрисовка прямоугольников и маркеров.
    - Определение центроидов объектов.
    """

    def __init__(self, renderer=None):
        """
        Инициализация Vision.
        :param renderer: Экземпляр ScreenRenderer для визуализации (опционально).
        """
        self.renderer = renderer

    @staticmethod
    def get_click_points(rectangles):
        """
        Определяет координаты центральных точек для списка прямоугольников.
        :param rectangles: Список прямоугольников [x, y, w, h].
        :return: Список центральных точек [(cx, cy), ...].
        """
        points = []
        for (x, y, w, h) in rectangles:
            center_x = x + int(w / 2)
            center_y = y + int(h / 2)
            points.append((center_x, center_y))
        return points

    def draw_rectangles(self, image, rectangles):
        """
        Отрисовывает прямоугольники на изображении и отправляет их в ScreenRenderer.
        :param image: Исходное изображение.
        :param rectangles: Список прямоугольников [x, y, w, h].
        :return: Изображение с нарисованными прямоугольниками.
        """
        for i, (x, y, w, h) in enumerate(rectangles):
            top_left = (x, y)
            bottom_right = (x + w, y + h)
            cv.rectangle(image, top_left, bottom_right, cfg.LINE_COLOR_RED, thickness=cfg.RECTANGLE_THICKNESS)

            # Если ScreenRenderer подключен, отправляем данные
            if self.renderer:
                self.renderer.add_element(
                    f"rectangle_{i}",
                    "rectangle",
                    {
                        "start": top_left,
                        "end": bottom_right,
                        "color": cfg.LINE_COLOR_RED,
                        "thickness": cfg.RECTANGLE_THICKNESS,
                    },
                )
        return image



    @staticmethod
    def centeroid(point_list):
        """
        Рассчитывает центроид (центр массы) для списка точек.
        :param point_list: Список точек [(x, y), ...].
        :return: Координаты центроида (cx, cy).
        """
        point_list = np.asarray(point_list, dtype=np.int32)
        length = point_list.shape[0]
        sum_x = np.sum(point_list[:, 0])
        sum_y = np.sum(point_list[:, 1])
        return [sum_x // length, sum_y // length]
