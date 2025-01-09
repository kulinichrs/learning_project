import numpy as np


def screen_to_world(mob_screen_x, mob_screen_y, screen_center_x, screen_center_y, camera_yaw, camera_distance):
    """
    Преобразует экранные координаты моба в игровые (пространственные).
    :param mob_screen_x: Координата моба по X на экране.
    :param mob_screen_y: Координата моба по Y на экране.
    :param screen_center_x: Центр экрана по X (позиция персонажа).
    :param screen_center_y: Центр экрана по Y (позиция персонажа).
    :param camera_yaw: Угол поворота камеры в градусах (азимут).
    :param camera_distance: Расстояние от камеры до персонажа.
    :return: Игровые координаты моба (x, y, z).
    """
    # Смещение моба относительно центра экрана
    dx = mob_screen_x - screen_center_x
    dy = mob_screen_y - screen_center_y

    # Угол поворота камеры в радианах
    yaw_radians = np.radians(camera_yaw)

    # Преобразование смещения в игровое пространство
    world_x = dx * np.cos(yaw_radians) - dy * np.sin(yaw_radians)
    world_y = dx * np.sin(yaw_radians) + dy * np.cos(yaw_radians)

    # Учитываем расстояние до камеры
    world_x *= camera_distance
    world_y *= camera_distance

    return world_x, world_y, 0  # Z-координата равна нулю, если плоскость игрового поля горизонтальна



class Mob:
    def __init__(self, x, y, w, h, id, frames_detected=0):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.id = id
        self.frames_detected = frames_detected
        self.missed_frames = 0  # Счётчик пропущенных кадров
        self.distance_to_character = None
        self.aggroed = False

    def update(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.frames_detected += 1
        self.missed_frames = 0  # Сбрасываем, если моб был обнаружен

    def increment_missed_frames(self):
        self.missed_frames += 1


    def calculate_distance_to_character(self, screen_center):
        """
        Вычисляет расстояние от моба до центра экрана (персонажа) в пикселях.
        :param screen_center: Центр экрана (screen_x, screen_y).
        """
        mob_center_x = self.x + self.w // 2
        mob_center_y = self.y + self.h // 2
        screen_center_x, screen_center_y = screen_center

        # Вычисляем расстояние до центра экрана
        self.distance_to_character = np.sqrt(
            (mob_center_x - screen_center_x) ** 2 +
            (mob_center_y - screen_center_y) ** 2
        )


    def get_center(self):
        return self.x + self.w // 2, self.y + self.h // 2
