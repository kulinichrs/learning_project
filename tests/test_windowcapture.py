from unittest import TestCase
import cv2 as cv
import time
import psutil
import config as cfg
from lib.windowcapture import WindowCapture

class TestWindowCapture(TestCase):

    def display_fps_and_cpu_usage(self, window_name="Window Capture"):
        """
        Захватывает изображение окна и отображает его с FPS и загрузкой процессора.
        :param window_name: Название окна для захвата.
        """
        # Инициализация захвата окна
        wincap = WindowCapture(window_name)

        # Статистика для FPS и загрузки CPU
        frame_times = []
        fps = 0
        cpu_usage = 0
        last_update_time = 0  # Таймер для обновления статистики

        # Запуск потока захвата
        wincap.start()
        try:
            while True:
                start_time = time.time()

                # Получаем текущий кадр
                with wincap.lock:
                    screenshot = wincap.screenshot

                if screenshot is not None:
                    # Рассчитываем средний FPS
                    frame_times.append(time.time() - start_time)
                    if len(frame_times) > 200:  # Поддерживаем статистику для последних 200 кадров
                        frame_times.pop(0)


                    # Обновляем статистику раз в 3 секунды
                    current_time = time.time()
                    if current_time - last_update_time >= 3:
                        cpu_usage = psutil.cpu_percent(interval=None)
                        fps = len(frame_times) / sum(frame_times) if frame_times else 0
                        last_update_time = current_time

                    # Добавляем текстовую информацию на изображение
                    cv.putText(screenshot, f"FPS: {fps:.2f}", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv.putText(screenshot, f"CPU: {cpu_usage:.2f}%", (10, 70), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0),
                               2)

                    # Отображаем изображение пользователю
                    cv.imshow("Window Capture with FPS and CPU", screenshot)

                # Обрабатываем выход
                if cv.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            # Останавливаем захват и закрываем окна
            wincap.stop()
            cv.destroyAllWindows()

    def test_start(self):
        WINDOW_NAME = "test.png - Windows Photo Viewer"  # Захват всего экрана. Для конкретного окна укажите его имя.
        self.display_fps_and_cpu_usage(WINDOW_NAME)
