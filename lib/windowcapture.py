import cv2
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
        Captures the current screenshot of the window or screen and applies posterization.
        :return: Posterized image as a Numpy array.
        """
        try:
            # Capture the screen using Win32 API
            wDC = win32gui.GetWindowDC(self.hwnd)
            dcObj = win32ui.CreateDCFromHandle(wDC)
            cDC = dcObj.CreateCompatibleDC()
            dataBitMap = win32ui.CreateBitmap()
            dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
            cDC.SelectObject(dataBitMap)
            cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

            # Convert to OpenCV format
            signedIntsArray = dataBitMap.GetBitmapBits(True)
            img = np.frombuffer(signedIntsArray, dtype='uint8')
            img = img.reshape((self.h, self.w, 4))

            # Release resources
            dcObj.DeleteDC()
            cDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, wDC)
            win32gui.DeleteObject(dataBitMap.GetHandle())

            # Remove alpha channel
            img = img[..., :3]

            # Reduce resolution if configured
            if cfg.REDUCE_RESOLUTION:
                img = cv2.resize(img, None, fx=cfg.RESIZE_SCALE, fy=cfg.RESIZE_SCALE, interpolation=cv2.INTER_AREA)

            # Apply posterization
            levels = 4  # You can adjust the number of levels (e.g., 4, 8, 16)
            img = self.posterize_image(np.ascontiguousarray(img), levels)

            return img

        except Exception as e:
            print(f"Error in get_screenshot: {e}")
            return None

    def posterize_image(self, image, levels):
        """
        Optimized: Posterizes an image by reducing the number of color levels using bitwise operations.
        :param image: Input image as a Numpy array (BGR format).
        :param levels: Number of color levels for each channel (e.g., 4, 8, 16).
        :return: Posterized image.
        """
        # Calculate the bit-shift based on the number of levels
        shift = 8 - int(np.log2(levels))  # For levels = 8 -> shift = 5 (256 >> 5 = 8 levels)

        # Apply bitwise operations to reduce color levels
        posterized_image = (image >> shift) << shift

        # Add an offset for better rounding to midpoints
        posterized_image += (1 << (shift - 1))

        return posterized_image

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