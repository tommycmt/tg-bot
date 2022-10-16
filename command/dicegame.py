import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, get_db_conn, get_command, get_user_name
from util.num2chinese import num2chinese

import pytz
from datetime import datetime
import random, time

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

choice_dict = {"big": "大",
               "small": "細",
               "same": "圍"}

def format_game_message(chat_id):
    dicegame = db_conn.dicegame
    doc = dicegame.find_one({"chatId":chat_id})
    message_id = doc["messageId"]
    round_no = doc["round"]
    bet_amount = doc["bet"]
    players = doc["players"]
    history = doc["history"]
    status = doc["status"]
    
    text = ""
    text += "買大細 - 第{}回 ({}精兵 局)\n".format(num2chinese(round_no), bet_amount)
    if (status != "end"):
        text += "現況:\n"
        if len(players) == 0:
            text += "未有人參戰\n"
        else:
            for player_id in players:
                player = players[player_id]
                if player["playing"] == False:
                    choice = "未參戰"
                elif player["choice"] == "":
                    choice = "未落注"
                else:
                    choice = choice_dict[player["choice"]]
                if player["money"] < bet_amount:
                    choice = "窮L"
                text += "{}: {}精兵 ({})\n".format(player["name"], player["money"], choice)
    else:
        text += "完局:\n"
        top_money = max([players[player_id]["money"] for player_id in players])
        for player_id in players:
            player = players[player_id]
            if player["money"] == top_money and player["money"] >= bet_amount:
                text += "{}: {}精兵 {}\n".format(player["name"], player["money"], "創蛇!?")
            else:
                text += "{}: {}精兵 {}\n".format(player["name"], player["money"], "窮L")
    if history["round"] != 0:
        if history["result"][0] == history["result"][1] and history["result"][0] == history["result"][2]:
            result = "圍骰通殺"
        else:
            sum_result = sum(history["result"])
            result = "{}點 {}".format(num2chinese(sum_result), "大" if sum_result >=11 else "細")
        text += "=================\n"
        text += "上回提要:\n"
        text += "{} {}\n".format("".join(map(num2chinese, history["result"])), result)
        for player_id in history["players"]:
            player = history["players"][player_id]
            if player["winning"] > 0:
                win_result = "贏"
            else:
                win_result = "賠"
            text += "{}: {} {}{}精兵 \n".format(player["name"], choice_dict[player["choice"]], win_result, abs(player["winning"]))
    return text, message_id, status

# format the inline keyboard button for callbackk
def format_dicegame_kb():
    custom_keyboard = [[telegram.InlineKeyboardButton(text="大", callback_data="dicebig"),
                        telegram.InlineKeyboardButton(text="細", callback_data="dicesmall"),
                        telegram.InlineKeyboardButton(text="圍骰", callback_data="dicesame")],
                       [telegram.InlineKeyboardButton(text="過大海啦", callback_data="dicejoin"),
                        telegram.InlineKeyboardButton(text="買蛋卷算", callback_data="dicequit")]]
    
    reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
    return reply_markup


def render(chat_id):
    text, message_id, status = format_game_message(chat_id)
    time.sleep(1)
    if status != "end":
        bot.edit_message_text(text, chat_id, message_id, reply_markup=format_dicegame_kb())
        return False
    else:
        bot.edit_message_text(text, chat_id, message_id)
        return True

def handle_dicegame(update):
    chat_id = update.message.chat_id
    dicegame = db_conn.dicegame
    doc = dicegame.find_one({"chatId":chat_id})
    if (update.message.text == "/dicegame clear"):
        try:
            dicegame.delete_one(doc)
            bot.delete_message(chat_id, doc["messageId"])
        except Exception as e:
            logger.warning(e)
        return
    if (update.message.text == "/dicegame kick"):
        try:
            players = doc["players"]
            for player_id in players:
                player = players[player_id]
                if player["diceTimestamp"].replace(tzinfo=pytz.utc).astimezone(tz).day  != datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz).day:
                    if player["choice"] == "" and player["playing"] == True:
                        player["playing"] = False
            not_playing = True
            for player_id in players:
                if players[player_id]["playing"]:
                    not_playing = False
            if not_playing:
                doc["status"] = "end"
            dicegame.save(doc)
            render(chat_id)
            if not_playing:
                dicegame.delete_one(doc)
            else:
                check_play(chat_id)
        except Exception as e:
            logger.warning(e)
        return
    if doc is not None:
        try:
            bot.delete_message(chat_id, doc["messageId"])
        except Exception as e:
            logger.warning(e)
        message = bot.send_message(chat_id=chat_id, text="請等等，我繽紛樂緊")
        message_id = message.message_id
        doc["messageId"] = message_id
        dicegame.save(doc)
        render(chat_id)
        check_play(chat_id)
        return
    text_messages = update.message.text.split()
    bet = 0
    if len(text_messages) >= 2 and get_command(text_messages[0]) == "dicegame":
        bet = min(max(int(text_messages[1]), 10), 100)
    else:
        update.message.reply_text("精兵呢")
        return
    
    message = bot.send_message(chat_id=chat_id, text="請等等，我繽紛樂緊")
    message_id = message.message_id
    dicegame.insert_one({"round": 1,
                         "bet": bet,
                         "messageId": message_id,
                         "chatId": chat_id,
                         "status": "playing",
                         "players": dict(),
                         "history": {"round": 0,
                                     "result": list(),
                                     "players": dict()}})
    render(chat_id)

def callback_dicegame(update):
    data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    callback_user_id = str(update.callback_query.from_user.id)
    dicegame = db_conn.dicegame
    doc = dicegame.find_one({"chatId": chat_id})
    players = doc["players"]
    bet_amount = doc["bet"]
    end = False
    if doc == None:
        bot.answer_callback_query(callback_query_id=update.callback_query.id, text="完左啦", show_alert=True)
        return
    if data == "dicebig" or data == "dicesmall" or data == "dicesame":
        #Case 1,2,3 big, small, same
        if callback_user_id not in players or not players[callback_user_id]["playing"]:
            bot.answer_callback_query(callback_query_id=update.callback_query.id, text="再玩斬手指", show_alert=True)
            return
        elif players[callback_user_id]["money"] < bet_amount:
            bot.answer_callback_query(callback_query_id=update.callback_query.id, text="留番去買蛋卷啦", show_alert=True)
            players[callback_user_id]["playing"] = False
            players[callback_user_id]["diceTimestamp"] = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz)
            doc["players"] = players
            dicegame.save(doc)
            end = render(chat_id)
        else:           
            if players[callback_user_id]["choice"] != "":
                bot.answer_callback_query(callback_query_id=update.callback_query.id, text="買定離手呀", show_alert=True)
                return
            else:
                players[callback_user_id]["choice"] = data.replace("dice","")
                players[callback_user_id]["diceTimestamp"] = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz)
                doc["players"] = players
                dicegame.save(doc)
                end = render(chat_id)
    elif data == "dicejoin":
        #Case 4 join
        if callback_user_id in players:
            if players[callback_user_id]["money"] < bet_amount:
                bot.answer_callback_query(callback_query_id=update.callback_query.id, text="唔歡迎窮L呀", show_alert=True)
                return
            elif not players[callback_user_id]["playing"]:
                players[callback_user_id]["playing"] = True
                players[callback_user_id]["diceTimestamp"] = datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz)
                doc["players"] = players
                dicegame.save(doc)
                end = render(chat_id)
            else:
                bot.answer_callback_query(callback_query_id=update.callback_query.id, text="再玩斬手指", show_alert=True)
                return
        else:
            user_name = get_user_name(update.callback_query.from_user)
            players.update({callback_user_id: {"name": user_name,
                                               "choice": "",
                                               "money": 1000,
                                               "playing": True,
                                               "diceTimestamp": datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(tz)}})
            dicegame.save(doc)
            end = render(chat_id)
    elif data == "dicequit":
        #Case 5 quit
        if callback_user_id in players:
            if players[callback_user_id]["playing"]:
                if players[callback_user_id]["choice"] == "":
                    players[callback_user_id]["playing"] = False
                    doc["players"] = players

                    not_playing = True
                    for player_id in players:
                        if players[player_id]["playing"]:
                            not_playing = False
                    if not_playing:
                        doc["status"] = "end"
                    dicegame.save(doc)
                    end = render(chat_id)
                    if end:
                        dicegame.delete_one(doc)
                else:
                    bot.answer_callback_query(callback_query_id=update.callback_query.id, text="想走數？", show_alert=True)
                    return
            else:
                bot.answer_callback_query(callback_query_id=update.callback_query.id, text="香港冇蛋卷喎", show_alert=True)
                return
        else:
            bot.answer_callback_query(callback_query_id=update.callback_query.id, text="香港冇蛋卷喎", show_alert=True)
            return
    check_play(chat_id)
    bot.answer_callback_query(callback_query_id=update.callback_query.id)
    
def check_play(chat_id):
    dicegame = db_conn.dicegame
    doc = dicegame.find_one({"chatId": chat_id})
    message_id = doc["messageId"]
    players = doc["players"]
    if (len(players) == 0):
        return
    for player_id in players:
        player = players[player_id]
        if player["choice"] == "" and player["playing"] == True:
            return
    dice_result, result = play()
    history_players = dict()
    for player_id in players:
        player = players[player_id]
        if player["playing"]:
            if player["choice"] == result:
                if result == "same":
                    winning = doc["bet"] * 24
                else:
                    winning = doc["bet"]
            else:
                winning = -doc["bet"]
            history_players.update({player_id: {"name": player["name"],
                                                "choice": player["choice"],
                                                "winning": winning}})
            player["money"] += winning
            player["choice"] = ""
    
    doc["history"]["round"] = doc["round"]
    doc["history"]["result"] = dice_result
    doc["history"]["players"] = history_players
    doc["players"] = players
    doc["round"] = doc["round"]+1
    if check_end(doc):
        doc["status"] = "end"
    dicegame.save(doc)
    end = render(chat_id)
    if end:
        dicegame.delete_one(doc)

def check_end(doc):
    players = doc["players"]
    bet_amount = doc["bet"]
    for player_id in players:
        player = players[player_id]
        if player["money"] >= bet_amount:
            return False
    return True

def play():
    dice_result = [random.randrange(1,7), random.randrange(1,7), random.randrange(1,7)]
    if dice_result[0] == dice_result[1] and dice_result[0] == dice_result[2]:
        result = "same"
    else:
        result = "big" if sum(dice_result) >=11 else "small"
    return  dice_result, result

            
