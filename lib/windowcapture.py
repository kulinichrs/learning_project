import cv2 as cv
import numpy as np
import win32gui, win32ui, win32con
from threading import Thread, Lock
from time import sleep, time
import config as cfg


class WindowCapture:
    """
    Класс для захвата изображения окна с возможностью управления нагрузкой на CPU.
    """

    def __init__(self, window_name=None):
        """
        Инициализация объекта WindowCapture:
        - Получает параметры окна или экрана.
        :param window_name: Название окна, если требуется захват конкретного окна.
        """
        self.lock = Lock()

        # Если имя окна не указано, захватываем весь экран
        if window_name is None:
            self.hwnd = win32gui.GetDesktopWindow()
        else:
            self.hwnd = win32gui.FindWindow(None, window_name)
            if not self.hwnd:
                raise Exception(f"Window not found: {window_name}")

        # Получение размеров окна
        window_rect = win32gui.GetWindowRect(self.hwnd)
        self.w = int((window_rect[2] - window_rect[0]) * cfg.WINDOW_SCALE)
        self.h = int((window_rect[3] - window_rect[1]) * cfg.WINDOW_SCALE)

        # Учет границ окна
        self.w -= cfg.BORDER_PIXELS * 2
        self.h -= cfg.TITLEBAR_PIXELS + cfg.BORDER_PIXELS
        self.cropped_x = cfg.BORDER_PIXELS
        self.cropped_y = cfg.TITLEBAR_PIXELS

        # Смещение для трансформации координат
        self.offset_x = window_rect[0] + self.cropped_x
        self.offset_y = window_rect[1] + self.cropped_y

        # Инициализация переменных захвата
        self.stopped = True
        self.screenshot = None
        self.capture_interval = cfg.LOAD_LIMIT_FRAMETIME  # Интервал захвата (секунды)

    def get_screenshot(self):
        """
        Захватывает текущий скриншот окна или экрана.
        :return: Numpy массив с изображением.
        """
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

        # Конвертация в формат OpenCV
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.frombuffer(signedIntsArray, dtype='uint8')
        img.shape = (self.h, self.w, 4)

        # Освобождение ресурсов
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # Удаление альфа-канала
        img = img[..., :3]

        # Уменьшение разрешения (если указано)
        if cfg.REDUCE_RESOLUTION:
            img = cv.resize(img, None, fx=cfg.RESIZE_SCALE, fy=cfg.RESIZE_SCALE, interpolation=cv.INTER_AREA)

        return np.ascontiguousarray(img)


    def simplify_image_colors(image, base_colors):
        """
        Упрощает цвета изображения, приводя их к ближайшим из заданной палитры.

        :param image: Исходное изображение в формате BGR (numpy array).
        :param base_colors: Список базовых цветов в формате BGR (list of tuples).
        :return: Изображение с упрощённой цветовой палитрой.
        """
        # Конвертируем изображение в формат float32 для вычислений
        image = image.astype(np.float32)

        # Преобразуем базовые цвета в numpy массив
        base_colors = np.array(base_colors, dtype=np.float32)

        # Создаем пустое изображение для упрощённых цветов
        simplified_image = np.zeros_like(image)

        # Для каждого пикселя ищем ближайший цвет из палитры
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                pixel = image[i, j]
                # Вычисляем расстояние до каждого базового цвета
                distances = np.linalg.norm(base_colors - pixel, axis=1)
                # Выбираем ближайший цвет
                closest_color = base_colors[np.argmin(distances)]
                simplified_image[i, j] = closest_color

        # Преобразуем обратно к uint8
        simplified_image = simplified_image.astype(np.uint8)
        return simplified_image

    # Пример использования
    if name == "__main__":
        # Задаём базовые цвета (BGR формат)
        base_colors = [
            (0, 0, 255),  # Красный
            (0, 255, 0),  # Зелёный
            (255, 0, 0),  # Синий
            (0, 255, 255),  # Жёлтый
            (255, 255, 0),  # Голубой
            (255, 0, 255),  # Фиолетовый
            (0, 0, 0),  # Чёрный
            (255, 255, 255)  # Белый
        ]

        # Загрузим изображение
        image = cv2.imread("input_image.jpg")

        # Упростим цвета
        simplified_image = simplify_image_colors(image, base_colors)

        # Сохраним результат
        cv2.imwrite("simplified_image.jpg", simplified_image)
        print("Изображение сохранено как simplified_image.jpg")

    @staticmethod
    def list_window_names():
        """
        Выводит список имен открытых окон. Полезно для отладки.
        """

        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                print(hex(hwnd), win32gui.GetWindowText(hwnd))

        win32gui.EnumWindows(winEnumHandler, None)

    def get_screen_position(self, pos):
        """
        Преобразует координаты пикселя на скриншоте в координаты экрана.
        :param pos: Координаты на скриншоте (x, y).
        :return: Координаты на экране (x, y).
        """
        return (pos[0] + self.offset_x, pos[1] + self.offset_y)

    def set_capture_interval(self, interval):
        """
        Устанавливает интервал между захватами.
        :param interval: Новый интервал в секундах.
        """
        self.capture_interval = max(interval, 0.01)

    def start(self):
        """
        Запускает процесс захвата изображения в отдельном потоке.
        """
        self.stopped = False
        Thread(target=self.run).start()

    def stop(self):
        """
        Останавливает процесс захвата изображения.
        """
        self.stopped = True

    def run(self):
        """
        Циклически обновляет скриншот с управлением нагрузкой на CPU.
        """
        while not self.stopped:
            start_time = time()

            screenshot = self.get_screenshot()
            with self.lock:
                self.screenshot = screenshot

            # Рассчитываем задержку для снижения нагрузки
            elapsed_time = time() - start_time
            sleep(max(0, self.capture_interval - elapsed_time))


def main():
    WindowCapture.list_window_names()

if __name__ == "__main__":
    main()