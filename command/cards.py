import telegram
import configparser
import logging

from util.common import get_bot, get_db_conn, get_command, get_user_name
from util.deck import Deck, Card, Hand

import random, time

bot = get_bot()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def handle_cards(update):
    deck = Deck(symbol=True)
    
    bot_cards = [deck.draw_one() for count in range(5)]
    bot_hand = Hand(bot_cards)
    bot_result = bot_hand.get_chi_ranking()
    
    player_cards = [deck.draw_one() for count in range(5)]
    player_hand = Hand(player_cards)
    player_result = player_hand.get_chi_ranking()

    winner = bot_hand.compare(player_hand, count_suit=True)

    if winner == 1:
        bot_win = "贏"
        player_win = "輸"
    elif winner == -1:
        bot_win = "輸"
        player_win = "贏"
    else:
        bot_win = "和"
        player_win = "和"
        
    reply  = "Gordon:\n"
    reply += "{}\n".format(bot_result)
    reply += "{} ({})\n".format(" ".join([str(card) for card in bot_cards]), bot_win)
    reply += "======================\n"
    reply += "{}:\n".format(get_user_name(update.message.from_user))
    reply += "{}\n".format(player_result)
    reply += "{} ({})\n".format(" ".join([str(card) for card in player_cards]), player_win)
    
    update.message.reply_text(reply)
    
