import numpy as np

from lib.mob import Mob
import config as cfg

class MobTracker:
    def __init__(self, max_distance=500, group_distance=30, buffer_frames=6, max_missed_frames=7):
        self.mobs = {}  # Хранение мобов: {id: Mob}
        self.next_id = 1
        self.max_distance = max_distance
        self.group_distance = group_distance
        self.buffer_frames = buffer_frames
        self.max_missed_frames = max_missed_frames  # Максимальное количество пропущенных кадров

    def update(self, detected_mobs, character_position):
        # Группируем близко расположенные мобы
        grouped_mobs = group_mobs_simple(detected_mobs, self.group_distance)

        updated_mobs = {}
        unmatched_mobs = grouped_mobs.copy()

        # Привязываем новые координаты к существующим мобам
        for mob_id, mob in self.mobs.items():
            mob_center = mob.get_center()
            matched_mob = None
            min_distance = float('inf')

            for mob_coords in unmatched_mobs:
                x, y, w, h = mob_coords
                distance = np.sqrt((x + w // 2 - mob_center[0]) ** 2 + (y + h // 2 - mob_center[1]) ** 2)
                if distance < self.max_distance and distance < min_distance:
                    matched_mob = mob_coords
                    min_distance = distance

            if matched_mob:
                x, y, w, h = matched_mob
                mob.update(x, y, w, h)
                mob.calculate_distance_to_character(character_position)
                updated_mobs[mob_id] = mob
                unmatched_mobs.remove(matched_mob)
            else:
                # Если моб не найден, увеличиваем missed_frames
                mob.increment_missed_frames()
                if mob.missed_frames < self.max_missed_frames:
                    updated_mobs[mob_id] = mob

        for mob_coords in unmatched_mobs:
            x, y, w, h = mob_coords
            new_mob = Mob(x, y, w, h, frames_detected=1, id =self.next_id)
            new_mob.calculate_distance_to_character(
                screen_center=(cfg.SCREEN_CENTER_X, cfg.SCREEN_CENTER_Y)
            )
            updated_mobs[self.next_id] = new_mob
            self.next_id += 1

        # Обновляем список мобов
        self.mobs = updated_mobs

        return self.mobs


def group_mobs_simple(detected_mobs, group_distance=30):
    """
    Группирует близко расположенные мобы на основе жадного алгоритма.
    :param detected_mobs: Список координат [(x, y, w, h)].
    :param group_distance: Максимальное расстояние для объединения объектов.
    :return: Группированные координаты мобов [(x, y, w, h)].
    """
    grouped = []
    used = set()  # Индексы уже обработанных мобов

    for i, (x1, y1, w1, h1) in enumerate(detected_mobs):
        if i in used:
            continue

        # Текущая группа
        group = [(x1, y1, w1, h1)]
        used.add(i)

        for j, (x2, y2, w2, h2) in enumerate(detected_mobs):
            if j in used:
                continue

            # Вычисляем расстояние между центрами мобов
            center1 = (x1 + w1 // 2, y1 + h1 // 2)
            center2 = (x2 + w2 // 2, y2 + h2 // 2)
            distance = np.sqrt((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2)

            if distance < group_distance:
                group.append((x2, y2, w2, h2))
                used.add(j)

        # Рассчитываем средние координаты для группы
        avg_x = int(np.mean([mob[0] for mob in group]))
        avg_y = int(np.mean([mob[1] for mob in group]))
        avg_w = int(np.mean([mob[2] for mob in group]))
        avg_h = int(np.mean([mob[3] for mob in group]))
        grouped.append((avg_x, avg_y, avg_w, avg_h))

    return grouped
