from pynput.mouse import Controller, Button

if __name__ == "__main__":
    # Создаем объект для управления мышью
    mouse = Controller()

    # Устанавливаем позицию мыши
    mouse.position = (500, 500)  # Устанавливаем позицию мыши на экран

    # Двигаем мышь на 100 пикселей вправо и 100 пикселей вниз
    mouse.move(100, 100)

    # Нажимаем и отпускаем кнопку мыши (например, левая кнопка)
    mouse.press(Button.left)
    mouse.release(Button.left)

