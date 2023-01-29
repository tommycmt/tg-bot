import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, get_db_conn, get_command, get_user_name
from util.num2chinese import num2chinese
from util.deck import Deck, Card

import pytz
from datetime import datetime
import random, time
import pickle

bot = get_bot()
db_conn = get_db_conn()
tz = pytz.timezone("Asia/Hong_Kong")

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# format the inline keyboard button for callbackk
def format_blackjack_kb():
    custom_keyboard = [[telegram.InlineKeyboardButton(text="官人我要", callback_data="blackjackcall"),
                        telegram.InlineKeyboardButton(text="官人我唔要", callback_data="blackjackfold")],
                       [telegram.InlineKeyboardButton(text="過大海啦", callback_data="blackjackjoin"),
                        telegram.InlineKeyboardButton(text="我條底底呢", callback_data="blackjackbase")]]
    
    reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
    return reply_markup

def format_message(doc):
    round_no = doc["round"]
    bet_amount = doc["bet"]
    bot_player = doc["botPlayer"]
    players = doc["players"]
    history = doc["history"]
    status = doc["status"]
    
    text = ""
    text += "21點 - 第{}回 ({}精兵 局)\n".format(num2chinese(round_no), bet_amount)
    if (status != "end"):
        text += "現況:\n"
        text += "莊 : {}精兵 ？  {}\n".format(bot_player["money"], " ".join(map(str, bot_player["cards"][1:])))
        for player_id in players:
            player = players[player_id]
            if player["playing"]:
                if get_result(player["cards"]) == "爆":
                    text += "{} : {}精兵 {} {}\n".format(player["name"], player["money"], " ".join(map(str, player["cards"])), get_result(player["cards"]))
                elif not player["canCall"]:
                    text += "{} : {}精兵 ？ {} ({})\n".format(player["name"], player["money"], " ".join(map(str, player["cards"][1:])), "夠")
                else:
                    text += "{} : {}精兵 ？ {} \n".format(player["name"], player["money"], " ".join(map(str, player["cards"][1:])))
            else:
                text += "{} : {}精兵 {}\n".format(player["name"], player["money"], "未落注")
    else:
        max_player_money = max([players[player_id]["money"] for player_id in players])
        
        text += "完局:\n"
        text += "莊 : {}精兵 {}\n".format(bot_player["money"], "創蛇!?" if bot_player["money"] >= max_player_money else "窮L")
        for player_id in players:
            player = players[player_id]
            text += "{} : {}精兵 {}\n".format(player["name"], player["money"], "創蛇!?" if player["money"] >= max_player_money and player["money"] >= bot_player["money"] else "窮L")
    if history["round"] != 0:
        text += "===============\n"
        text += "上回提要:\n"
        text += "莊 : {}精兵 {} {}\n".format(history["botPlayer"]["winning"], " ".join(map(str,history["botPlayer"]["cards"])), get_result(history["botPlayer"]["cards"]))
        for player_id in history["players"]:
            player = history["players"][player_id]
            text += "{} : {}精兵 {} {}\n".format(player["name"], player["winning"], " ".join(map(str,player["cards"])), get_result(player["cards"]))      
    return text


async def render(chat_id, doc):
    text = format_message(doc)
    status = doc["status"]
    message_id = doc["messageId"]
    if status != "end":
        await bot.edit_message_text(text, chat_id, message_id, reply_markup=format_blackjack_kb())
    else:
        await bot.edit_message_text(text, chat_id, message_id)

async def handle_blackjack(update):
    chat_id = update.message.chat_id
    text = update.message.text.lower()
    blackjack = db_conn.blackjack
    doc = blackjack.find_one({"chatId":chat_id})
    if doc is not None:
        doc = load(doc)
        if doc["status"] == "end":
            try:
                doc = save(doc)
                blackjack.delete_one(doc)
                message = await bot.send_message(chat_id=chat_id, text="請等等，我繽紛樂緊")
                message_id = message.message_id
                deck = Deck(symbol=True)
                bot_cards = [deck.draw_one(), deck.draw_one()]
                blackjack.insert_one({"round": 1,
                                      "bet": 10,
                                      "messageId": message_id,
                                      "chatId": chat_id,
                                      "status": "waiting",
                                      "deck": pickle.dumps(deck),
                                      "botPlayer": {"cards": pickle.dumps(bot_cards),
                                                    "money": 1000,
                                                    "playing": True,
                                                    "canCall": True},
                                      "players": dict(),
                                      "history": {"round": 0,
                                                  "botPlayer": dict(),
                                                  "players": dict()}})
                doc = blackjack.find_one({"chatId":chat_id})
                doc = load(doc)
                await render(chat_id, doc)
            except Exception as e:
                logger.warning(e)
            return
        if (update.message.text == "/blackjack clear"):
            try:
                doc = save(doc)
                blackjack.delete_one(doc)
                await bot.delete_message(chat_id, doc["messageId"])
            except Exception as e:
                logger.warning(e)
            return
        elif (update.message.text == "/blackjack kick"):
            try:
                bet_amount = doc["bet"]
                players = doc["players"]
                for player_id in players:
                    player = players[player_id]
                    if player["canCall"] and player["playing"] and (datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz) - player["joinTimestamp"].replace(tzinfo=pytz.utc).astimezone(tz)).seconds >= 3600:
                        player["money"] -= bet_amount
                        player["cards"] = []
                        player["playing"] = False
                        player["canCall"] = False
            except Exception as e:
                logger.warning(e)
        else:
            try:
                await bot.delete_message(chat_id, doc["messageId"])
            except Exception as e:
                logger.warning(e)
            message = await bot.send_message(chat_id=chat_id, text="請等等，我繽紛樂緊")
            message_id = message.message_id
            doc["messageId"] = message_id
        doc = check_start(doc)
        await render(chat_id, doc)
        doc = save(doc)
        blackjack.replace_one({'_id': doc['_id']}, doc, upsert=True)
    else:
        message = await bot.send_message(chat_id=chat_id, text="請等等，我繽紛樂緊")
        message_id = message.message_id
        deck = Deck(symbol=True)
        bot_cards = [deck.draw_one(), deck.draw_one()]
        blackjack.insert_one({"round": 1,
                              "bet": 10,
                              "messageId": message_id,
                              "chatId": chat_id,
                              "status": "waiting",
                              "deck": pickle.dumps(deck),
                              "botPlayer": {"cards": pickle.dumps(bot_cards),
                                            "money": 1000,
                                            "playing": True,
                                            "canCall": True},
                              "players": dict(),
                              "history": {"round": 0,
                                          "botPlayer": dict(),
                                          "players": dict()}})
        doc = blackjack.find_one({"chatId":chat_id})
        doc = load(doc)
        await render(chat_id, doc)

async def callback_blackjack(update):
    data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    callback_user_id = str(update.callback_query.from_user.id)
    blackjack = db_conn.blackjack
    doc = blackjack.find_one({"chatId": chat_id})
    if doc == None:
        await bot.answer_callback_query(callback_query_id=update.callback_query.id, text="完左啦", show_alert=True)
        return
    doc = load(doc)
    bet_amount = doc["bet"]
    deck = doc["deck"]
    players = doc["players"]
    if data == "blackjackcall":
        if callback_user_id in players and players[callback_user_id]["playing"]:
            if players[callback_user_id]["canCall"]:
                players[callback_user_id]["joinTimestamp"] = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz)
                players[callback_user_id]["cards"].append(deck.draw_one())
                doc["deck"] = deck
                doc["players"] = players
            else:
                await bot.answer_callback_query(callback_query_id=update.callback_query.id, text="冇得要啦", show_alert=True)
                return
        else:
            await bot.answer_callback_query(callback_query_id=update.callback_query.id, text="香港冇做生意呀", show_alert=True)
            return
    if data == "blackjackfold":
        if callback_user_id in players and players[callback_user_id]["playing"]:
            if players[callback_user_id]["canCall"]:
                players[callback_user_id]["canCall"] = False
                players[callback_user_id]["joinTimestamp"] = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz)
                doc["deck"] = deck
                doc["players"] = players
            else:
                await bot.answer_callback_query(callback_query_id=update.callback_query.id, text="再玩斬手指", show_alert=True)
                return
        else:
            await bot.answer_callback_query(callback_query_id=update.callback_query.id, text="香港冇做生意呀", show_alert=True)
            return
    if data == "blackjackjoin":
        if callback_user_id in players:
            if players[callback_user_id]["money"] < bet_amount:
                await bot.answer_callback_query(callback_query_id=update.callback_query.id, text="唔歡迎窮L呀", show_alert=True)
                return
            elif not players[callback_user_id]["playing"]:
                players[callback_user_id]["playing"] = True
                players[callback_user_id]["canCall"] = True
                players[callback_user_id]["joinTimestamp"] = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz)
                players[callback_user_id]["cards"] = [deck.draw_one(), deck.draw_one()]
                doc["deck"] = deck
                doc["status"] = "playing"
                doc["players"] = players
            else:
                await bot.answer_callback_query(callback_query_id=update.callback_query.id, text="再玩斬手指", show_alert=True)
                return
        else:
            user_name = get_user_name(update.callback_query.from_user)        
            players.update({callback_user_id: {"name": user_name,
                                               "cards": [deck.draw_one(), deck.draw_one()],
                                               "money": 1000,
                                               "playing": True,
                                               "canCall": True,
                                               "joinTimestamp": datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz)}})
            doc["status"] = "playing"
            doc["deck"] = deck
            doc["players"] = players
    if data == "blackjackbase":
        if callback_user_id in players and players[callback_user_id]["playing"]:
            await bot.answer_callback_query(callback_query_id=update.callback_query.id, text=str(players[callback_user_id]["cards"][0]), show_alert=True)
            return
        else:
            await bot.answer_callback_query(callback_query_id=update.callback_query.id, text="我好懷疑你有冇底底", show_alert=True)
            return
    doc = check_start(doc)
    await render(chat_id, doc)
    doc = save(doc)
    blackjack.replace_one({'_id': doc['_id']}, doc, upsert=True)
    await bot.answer_callback_query(callback_query_id=update.callback_query.id)

def check_start(doc):
    bet_amount = doc["bet"]
    deck = doc["deck"]
    players = doc["players"]
    bot_player = doc["botPlayer"]

    if doc["status"] == "waiting" or doc["status"] == "end":
        return doc

    for player_id in players:
        player = players[player_id]
        if player["playing"] and player["canCall"]:
            if check_explode(player["cards"]):
                player["canCall"] = False

                
    for player_id in players:
        player = players[player_id]
        if player["playing"] and player["canCall"]:
            return doc

    if not blackjack(bot_player["cards"]):
        while check_bot_call(bot_player["cards"]):
            bot_player["cards"].append(deck.draw_one())



    history = dict()
    history["round"] = doc["round"]
    history["botPlayer"] = {"cards": bot_player["cards"],
                            "winning": 0}
    history["players"] = dict()
    for player_id in players:
        player = players[player_id]
        history["players"][player_id] = {"name": player["name"],
                                         "cards": player["cards"],
                                         "winning": 0}
        

    if check_explode(bot_player["cards"]):
        for player_id in players:
            player = players[player_id]
            if player["playing"] and check_explode(player["cards"]) == False:
                if blackjack(player["cards"]) or jack(player["cards"]):
                    history["botPlayer"]["winning"] -= 2 * bet_amount
                    history["players"][player_id]["winning"] += 2 * bet_amount
                else:
                    history["botPlayer"]["winning"] -= bet_amount
                    history["players"][player_id]["winning"] += bet_amount
            elif player["playing"] and check_explode(player["cards"]):
                history["botPlayer"]["winning"] += bet_amount
                history["players"][player_id]["winning"] -= bet_amount
    else:
        for player_id in players:
            player = players[player_id]
            if player["playing"] and check_explode(player["cards"]) == False:
                winner, amount = compare(bot_player["cards"], player["cards"])
                if winner == "bot":
                    history["botPlayer"]["winning"] += amount * bet_amount
                    history["players"][player_id]["winning"] -= amount * bet_amount
                elif winner == "player":
                    history["botPlayer"]["winning"] -= amount * bet_amount
                    history["players"][player_id]["winning"] += amount * bet_amount
            elif player["playing"] and check_explode(player["cards"]):
                history["botPlayer"]["winning"] += bet_amount
                history["players"][player_id]["winning"] -= bet_amount

    for player_id in history["players"]:
        players[player_id]["money"] += history["players"][player_id]["winning"]
    bot_player["money"] += history["botPlayer"]["winning"]
    
    if  min([players[player_id]["money"] for player_id in players]+[bot_player["money"]]) < bet_amount and doc["status"] == "playing":
        doc["status"] = "end"


    doc["history"] = history
    if doc["status"] != "end":
        doc["status"] = "waiting"
        deck = Deck(symbol=True)
        bot_cards = [deck.draw_one(), deck.draw_one()]
        doc["botPlayer"]["cards"] = bot_cards
        doc["botPlayer"]["canCall"] = True
        doc["deck"] = deck
        doc["round"] += 1
        if doc["round"] % 5 == 0:
            doc["bet"] += 10
    for player_id in players:
        player = players[player_id]
        player["canCall"] = True
        player["cards"] = []
        player["playing"] = False
    doc["players"] = players
    

    return doc

def count_pt(cards):
    pt_dict = {"A": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "T": 10, "J": 10, "Q": 10, "K": 10}
    total_1 = 0
    total_2 = 0
    ace = False
    for card in cards:
        if card.rank == "A" and ace == False:
            total_2 += 11
            ace = True
        elif card.rank == "A":
            total_2 += 1
        else:
            total_2 += pt_dict[card.rank]
        total_1 += pt_dict[card.rank]
    return total_1, total_2
    
def check_explode(cards):
    total_1, total_2 = count_pt(cards)
    if total_1 > 21 and total_2 > 21:
        return True
    return False


def check_bot_call(cards):
    total_1, total_2 = count_pt(cards)
    if total_1 < 17 and total_2 < 17:
        return True
    if total_1 < 17 and total_2 > 21:
        return True
    if total_1 > 21 and total_2 < 17:
        return True
    return False

def blackjack(cards):
    total_1, total_2 = count_pt(cards)
    if len(cards) == 2 and (total_1 == 21 or total_2 == 21):
        return True
    return False


def jack(cards):
    total_1, total_2 = count_pt(cards)
    if (total_1 == 21 or total_2 == 21):
        return True
    return False

def get_result(cards):
    if check_explode(cards):
        return "爆"
    if blackjack(cards):
        return "blackjack"
    if jack(cards):
        return "21點"
    total_1, total_2 = count_pt(cards)
    return str(total_2 if total_2 <= 21 and total_2 > total_1 else total_1) + "點"

def compare(bot_cards, player_cards):
    if blackjack(bot_cards):
        if blackjack(player_cards):
            return "draw", 0
        else:
            return "bot", 2
    if jack(bot_cards):
        if blackjack(player_cards):
            return "player", 2
        elif jack(player_cards):
            return "draw", 0
        else:
            return "bot", 2
    bot_total_1, bot_total_2 = count_pt(bot_cards)
    bot_total = bot_total_2 if bot_total_2 <= 21 and bot_total_2 > bot_total_1 else bot_total_1
    if blackjack(player_cards):
        return "player", 2
    elif jack(player_cards):
        return "player", 2
    else:
        player_total_1, player_total_2 = count_pt(player_cards)
        player_total = player_total_2 if player_total_2 <= 21 and player_total_2 > player_total_1 else player_total_1
        if bot_total > player_total:
            return "bot", 1
        elif bot_total < player_total:
            return "player", 1
        else:
            return "draw", 0
    return "draw", 0


def load(doc):
    doc["deck"] = pickle.loads(doc["deck"])
    doc["botPlayer"]["cards"] = pickle.loads(doc["botPlayer"]["cards"])
    for player_id in doc["players"]:
        doc["players"][player_id]["cards"] = pickle.loads(doc["players"][player_id]["cards"])
    if doc["history"]["round"] != 0:
        doc["history"]["botPlayer"]["cards"] = pickle.loads(doc["history"]["botPlayer"]["cards"])
        for player_id in doc["history"]["players"]:
            doc["history"]["players"][player_id]["cards"] = pickle.loads(doc["history"]["players"][player_id]["cards"])
    return doc


def save(doc):
    doc["deck"] = pickle.dumps(doc["deck"])
    doc["botPlayer"]["cards"] = pickle.dumps(doc["botPlayer"]["cards"])
    for player_id in doc["players"]:
        doc["players"][player_id]["cards"] = pickle.dumps(doc["players"][player_id]["cards"])
    if doc["history"]["round"] != 0:
        doc["history"]["botPlayer"]["cards"] = pickle.dumps(doc["history"]["botPlayer"]["cards"])
        for player_id in doc["history"]["players"]:
            doc["history"]["players"][player_id]["cards"] = pickle.dumps(doc["history"]["players"][player_id]["cards"])
    return doc
