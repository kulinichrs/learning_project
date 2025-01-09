

from lib.states.botstate import BotState
import config as cfg
from pynput.mouse import Controller, Button

import time
from time import sleep



class AttackState(BotState):
    def handle(self, bot):
        # Переключаемся на ближний бой
        # if bot.current_weapon != "main":
        #     bot.switch_weapon("main")
        if not bot.have_target:
            bot.state_manager.set_state(LootState())
        # elif not bot.have_target and bot.have_close_targets_left:
        #     bot.state_manager.set_state(SearchLeftMobsState())
        else:
            bot.attack_target()

class BuffingState(BotState):
    def handle(self, bot):
        if  bot.have_target:
            bot.state_manager.set_state(AttackState())
        bot.rebuff()
        if not bot.have_animus and bot.animus_last_see_time < time.time():
            bot.state_manager.set_state(SummoningState())
        else:
            bot.state_manager.set_state(SearchState())

class LootState(BotState):
    def handle(self, bot):
        if  bot.have_target:
            bot.state_manager.set_state(AttackState())
        bot.loot_mobs()
        bot.kill_counter += len(bot.mobs)
        bot.mobs.clear()
        bot.state_manager.set_state(BuffingState())


class RotateState(BotState):
    def handle(self, bot):
        if  bot.have_target:
            bot.state_manager.set_state(AttackState())
        bot.rotate()
        bot.state_manager.set_state(SearchState())

#
# class SearchLeftMobsState(BotState):
#     def handle(self, bot):
#         if bot.have_target:
#             bot.state_manager.set_state(AttackState())
#         if bot.have_close_targets_left:
#             nearest_mob = min(bot.mobs, key=lambda mob: mob.distance_to_character)
#             bot.mouse.position = nearest_mob.get_center()
#             bot.mouse.press(Button.left)
#             sleep(0.1)
#             bot.mouse.release(Button.left)
#             sleep(2)
#
#         else:
#             bot.state_manager.set_state(LootState())


class SearchState(BotState):
    retry_count = 0
    max_retries = 5
    def handle(self, bot):
        while self.retry_count < self.max_retries:
            if bot.have_target:
                bot.state_manager.set_state( AttackState())
                return

            elif len(bot.mobs) == 0:
                bot.state_manager.set_state(RotateState())
                return

            # elif cfg.BOT_MASS_FARM_MODE:
            #     bot.state_manager.set_state(AggroMobsState())
            #     return
            else:
                bot.select_target()
                sleep(1)
                if bot.have_target:
                    return
                else:
                    self.retry_count += 1
        bot.state_manager.set_state(RotateState())


class StartState(BotState):
    def handle(self, bot):
        bot.state_manager.set_state(BuffingState())
        sleep(0.2)


class SummoningState(BotState):
    def handle(self, bot):
        if bot.have_target:
            bot.state_manager.set_state(AttackState())
        if cfg.USE_ANIMUS:
            bot.summon_animus()
        bot.state_manager.set_state( SearchState())