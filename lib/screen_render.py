import cv2 as cv
import time
from threading import Lock, Thread
from lib.windowcapture import WindowCapture
import psutil  # Для мониторинга системных ресурсов

class ScreenRenderer:
    """
    Отвечает за получение кадров и отрисовку объектов на экране, с мониторингом ресурсов.
    """

    def __init__(self, window_name=None, wincap=None):
        self.wincap = wincap
        if wincap is None:
            self.wincap = WindowCapture(window_name)
        self.wincap.start()
        self.lock = Lock()
        self.elements = {}  # Словарь отрисовываемых элементов {id: параметры}
        self.stopped = False
        self.start_time = time.time()  # Время запуска
        self.process = psutil.Process()  # Информация о текущем процессе
        self.last_system_info_time = 0  # Последнее время обновления системной информации
        self.system_info = ""  # Текущая строка системной информации

    def add_element(self, identifier, element_type, params, mob=False):
        """
        Добавляет или обновляет элемент для отрисовки.
        :param identifier: Уникальный текстовый идентификатор элемента.
        :param element_type: Тип элемента ("rectangle", "text", "circle" и т.д.).
        :param params: Параметры элемента (координаты, цвет и т.д.).
        :param mob: Флаг, указывающий, является ли элемент мобом (по умолчанию False).
        """
        with self.lock:
            self.elements[identifier] = {"type": element_type, "params": params, "mob": mob}

    def remove_mob_elements(self):
        """
        Удаляет все элементы, у которых параметр mob=True.
        """
        with self.lock:
            # Проходим по всем элементам и удаляем те, у которых mob=True
            to_remove = [key for key, value in self.elements.items() if value["mob"]]
            for key in to_remove:
                del self.elements[key]

    def remove_element(self, identifier):
        """
        Убирает элемент из списка по идентификатору.
        :param identifier: Уникальный текстовый идентификатор элемента.
        """
        with self.lock:
            if identifier in self.elements:
                del self.elements[identifier]

    def update_system_info(self):
        """
        Обновляет системную информацию не чаще одного раза в секунду.
        """
        current_time = time.time()
        if current_time - self.last_system_info_time < 1:
            return  # Не обновляем чаще одного раза в секунду

        self.last_system_info_time = current_time

        # Загрузка CPU и память текущего процесса
        cpu_percent = psutil.cpu_percent(interval=None)  # Загрузка процессора (%)
        memory_info = self.process.memory_info().rss // (1024 * 1024)  # Память текущего процесса (MB)

        # Время работы в формате HH24:mm:ss
        uptime_seconds = int(current_time - self.start_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        uptime = f"{hours:02}:{minutes:02}:{seconds:02}"

        self.system_info = f"CPU: {cpu_percent:.1f}% | Memory: {memory_info}MB | Uptime: {uptime}"

    def draw_text_with_outline(self, frame, text, position, font_scale=0.5, color=(200, 200, 200), thickness=1):
        """
        Рисует текст с контуром на кадре.
        :param frame: Кадр для отрисовки.
        :param text: Текст для отображения.
        :param position: Позиция текста (x, y).
        :param font_scale: Размер шрифта.
        :param color: Цвет текста (BGR).
        :param thickness: Толщина текста.
        """
        # Рисуем черный контур
        cv.putText(frame, text, position, cv.FONT_HERSHEY_DUPLEX, font_scale, (0, 0, 0), thickness + 2)
        # Рисуем основной текст
        cv.putText(frame, text, position, cv.FONT_HERSHEY_DUPLEX, font_scale, color, thickness)

    def draw_circle(self, frame, center, radius, color, thickness):
        """
        Рисует круг на кадре.
        :param frame: Кадр для отрисовки.
        :param center: Центр круга (x, y).
        :param radius: Радиус круга.
        :param color: Цвет круга (BGR).
        :param thickness: Толщина линии.
        """
        cv.circle(frame, center, radius, color, thickness)

    def render(self):
        """
        Основной метод отрисовки экрана с добавленными элементами.
        """
        fps_limit = 60  # Лимит FPS
        frame_duration = 1.0 / fps_limit

        while not self.stopped:
            start_time = time.time()

            with self.wincap.lock:
                frame = self.wincap.screenshot
                if frame is None:
                    # print("Failed to capture screenshot. Retrying...")
                    continue
                frame = frame.copy()

            # Рисуем элементы
            with self.lock:
                for identifier, element in self.elements.items():
                    element_type = element["type"]
                    params = element["params"]

                    if element_type == "rectangle":
                        cv.rectangle(frame, params["start"], params["end"], params["color"], params["thickness"])
                    elif element_type == "text":
                        self.draw_text_with_outline(
                            frame,
                            params["text"],
                            params["position"],
                            params["font_scale"],
                            params["color"],
                            params["thickness"],
                        )
                    elif element_type == "circle":
                        self.draw_circle(
                            frame,
                            params["center"],
                            params["radius"],
                            params["color"],
                            params["thickness"],
                        )

            # Обновляем системную информацию
            self.update_system_info()

            # Добавляем системную информацию в верхний левый угол
            self.draw_text_with_outline(frame, self.system_info, (10, 30), font_scale=0.5, color=(248, 248, 255))

            # Отображаем результирующий кадр
            cv.imshow("Game Screen", frame)

            # Рассчитываем задержку для соблюдения FPS
            elapsed_time = time.time() - start_time
            sleep_time = max(0, frame_duration - elapsed_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

            # Обрабатываем нажатие клавиш
            key = cv.waitKey(1) & 0xFF
            if key == ord("q"):  # Нажмите 'q', чтобы выйти
                self.stopped = True

        self.wincap.stop()
        cv.destroyAllWindows()

    def stop(self):
        """
        Останавливает процесс отрисовки.
        """
        print(f"Renderer(id={self}) stopped ")
        self.stopped = True

    def start(self):
        print(f"Renderer(id={self}) starting ")
        self.stopped = False
        Thread(target=self.render, daemon=True).start()
