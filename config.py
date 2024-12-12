# Configuration file for constants used in the project.

# General scale percentage for image resizing
SCALE_PERCENT = 50  # Shrinks the image to 30% of its original size for display.
RESIZE_SCALE = 0.5  # Коэффициент уменьшения (например, 0.5 для 50%)
WINDOW_SCALE = 2  # Scale for window capture.

# Circle radii for visualization
CIRCLE_RADIUS_LARGE = 15  # Large radius for detection visualization.
CIRCLE_RADIUS_MEDIUM = 10  # Medium radius for bot's targets.
CIRCLE_RADIUS_SMALL = 5  # Small radius for possible target.

# Delay for key wait in milliseconds
KEY_WAIT_MS = 100  # Delay for OpenCV key listener.

# Bot runtime settings
BOT_RUNTIME_LIMIT_HOURS = 2  # Maximum bot runtime in hours.
MOB_IGNORE_TIMEOUT_SECONDS = 180  # Timeout for ignoring mobs in seconds.
ATTACK_VALID_TIMEOUT_SECONDS = 3  # Timeout for attack validation in seconds.
REBUFF_TIMEOUT_SECODS = 108
ANIMUS_TIMEOUT_SECODS = 120

# Color ranges for attack and detection
COLOR_ATTACK_R_RANGE = (80, 255)  # Red channel range for attack color.
COLOR_ATTACK_G_RANGE = (80, 255)  # Green channel range for attack color.
COLOR_ATTACK_B_RANGE = (0, 120)  # Blue channel range for attack color.

COLOR_YELLOW_LOWER = [20, 75, 75]  # Lower bound for yellow color detection.
COLOR_YELLOW_UPPER = [43, 255, 255]  # Upper bound for yellow color detection.

# Colors for visualization
LINE_COLOR_RED = (0, 0, 255)  # Red color for rectangle lines.
MARKER_COLOR_MAGENTA = (255, 0, 255)  # Magenta color for markers.


BORDER_PIXELS = 0  # Number of pixels to ignore for the border.
TITLEBAR_PIXELS = 0  # Number of pixels to ignore for the title bar.

# Области анализа (координаты x, y верхнего левого и нижнего правого угла)
TARGET_AREA = [[387, 264], [580, 288]]  # Область для проверки наличия цели
ANIMUS_AREA = [[135, 290], [148, 302]]  # Область для проверки анимуса
BUFFS_AREA = [[930, 345], [971, 526]]  # Область для проверки баффов
SKILL_PANEL_AREA = [[336, 773], [525, 831]]  # Область панели скиллов
HP_BAR_AREA = [[0, 210], [191, 283]]  # Область полоски HP/SP
CHAT_AREA = [[0, 657], [300, 853]]  # Область чата
RADAR_AREA = [[847, 222], [966, 296]]  # Область радара
TOP_AREA = [[0, 0], [978, 256]]
BOTTOM_AREA = [[0, 769], [968, 1030]]

MYMP_DOT = [88, 256]
MYMP_DOT_COLOR = [200, 41, 41]
MYHP_DOT = [75, 247]
MYHP_DOT_COLOR = [3, 10, 211]
TARGET_DOT1 = [394, 260]
TARGET_DOT1_COLOR = [55, 60, 66]
TARGET_DOT2 = [406, 284]
TARGET_DOT2_COLOR = [109, 197, 223]
TARGET_MAX_HP_DOT = [550, 272]
TARGET_MAX_HP_DOT_COLOR = [18, 13, 165]
ANIMUS_HP_DOT = [35, 289]
ANIMUS_HP_DOT_COLOR = [34, 35, 189]
ANIMUS_EXIT_DOT = [136, 295]
ANIMUS_EXIT_DOT_COLOR = [237, 239, 249]
SKILL_DOT = [418, 801]
SKILL_DOT_COLOR = [248, 88, 126]

# Интервалы проверки состояний
RECTANGLE_THICKNESS = 2  # Толщина линий прямоугольников
LOAD_LIMIT_FRAMETIME = 0.07  # Интервал в секундах

REDUCE_RESOLUTION = True  # Включить уменьшение разрешения



