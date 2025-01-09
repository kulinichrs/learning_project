from time import sleep


class BotStateManager:
    def __init__(self, initial_state):
        self.current_state = initial_state

    def handle(self, bot):
        if self.current_state:
            self.current_state.handle(bot)

    def set_state(self, new_state):
        self.current_state = new_state
        sleep(0.2)