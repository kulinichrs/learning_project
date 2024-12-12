import unittest
import numpy as np
import cv2 as cv
import datetime
from lib.detection import Detection
from lib.screen_render  import ScreenRenderer
import config as cfg


class TestDetection(unittest.TestCase):
    def setUp(self):
        """
        Подготовка данных для тестов.
        """
        # Создаем экземпляр Detection без ScreenRenderer
        self.detection = Detection(renderer=None)
        # Создаем экземпляр Detection с ScreenRenderer (для отладки)
        self.renderer = ScreenRenderer("test.png - Windows Photo Viewer")
        self.detection_with_renderer = Detection(renderer=self.renderer)

        # Создаем тестовые изображения
        self.test_screenshot = np.zeros((500, 500, 3), dtype=np.uint8)
        self.test_mask = np.zeros((500, 500), dtype=np.uint8)
        cv.rectangle(self.test_mask, (100, 100), (200, 200), 255, -1)  # Белый квадрат

        # Тестовый шаблон
        self.test_template = np.zeros((50, 50), dtype=np.uint8)
        cv.rectangle(self.test_template, (10, 10), (40, 40), 255, -1)

    def test_initialization(self):
        """
        Проверяем, что объект инициализируется корректно.
        """
        self.assertIsInstance(self.detection, Detection)
        self.assertFalse(self.detection.have_target)
        self.assertFalse(self.detection.have_buffs)
        self.assertFalse(self.detection.have_animus)

    def test_update_screenshot(self):
        """
        Проверяем, что метод update корректно обновляет скриншот.
        """
        self.detection.update(self.test_screenshot)
        with self.detection.lock:
            np.testing.assert_array_equal(self.detection.screenshot, self.test_screenshot)

    def test_get_char_data(self):
        """
        Проверяем, что get_char_data возвращает корректные данные.
        """
        self.detection.have_target = True
        self.detection.have_buffs = True
        self.detection.have_animus = True
        char_data = self.detection.get_char_data()

        self.assertEqual(char_data[0], True)  # Проверяем цель
        self.assertEqual(char_data[1], True)  # Проверяем баффы
        self.assertEqual(char_data[2], True)  # Проверяем анимус
        self.assertIsInstance(char_data[4], list)  # Проверяем координаты мобов

    def test_contains_template(self):
        """
        Проверяем корректность работы поиска шаблонов.
        """
        # Вставляем шаблон в тестовый скриншот
        self.test_screenshot[150:200, 150:200] = 255
        result = self.detection.contains_template(self.test_screenshot, self.test_template, threshold=0.8)
        self.assertTrue(result)

        # Проверяем отсутствие совпадения
        self.test_screenshot.fill(0)
        result = self.detection.contains_template(self.test_screenshot, self.test_template, threshold=0.8)
        self.assertFalse(result)

    def test_filter_mask(self):
        """
        Проверяем, что метод filter_mask корректно исключает области.
        """
        # Создаем область для исключения
        filter_area = ((100, 100), (200, 200))

        # Фильтруем маску
        filtered_mask = self.detection.filter_mask(self.test_mask.copy(), filter_area)

        # Проверяем, что область исключена
        self.assertTrue(np.all(filtered_mask[100:200, 100:200] == 0))
        # Проверяем, что остальные области не изменились
        self.assertTrue(np.all(filtered_mask[0:100, 0:100] == self.test_mask[0:100, 0:100]))

    def test_visualize_debug_info(self):
        """
        Проверяем, что метод visualize_debug_info добавляет элементы в ScreenRenderer.
        """
        mobs_coordinates = [[150, 150], [300, 300]]
        self.detection_with_renderer.visualize_debug_info(self.test_mask, mobs_coordinates)

        # Проверяем, что элементы добавлены в ScreenRenderer
        self.assertIn("mob_mask", self.renderer.elements)
        self.assertEqual(len(self.renderer.elements), 3)  # 1 маска + 2 моба
        self.assertIn("mob_0", self.renderer.elements)
        self.assertIn("mob_1", self.renderer.elements)

    def test_run_limited_iterations(self):
        """
        Проверяем, что поток run корректно работает в ограниченном режиме.
        """
        self.detection.update(self.test_screenshot)

        # Запускаем поток на ограниченное время
        self.detection.start()
        sleep_time = 0.2  # Даем время на выполнение итераций
        self.detection.stop()

        # Проверяем, что run завершился корректно
        self.assertFalse(self.detection.stopped)

    def tearDown(self):
        """
        Завершение тестов, освобождение ресурсов.
        """
        if self.renderer:
            self.renderer.stop()
