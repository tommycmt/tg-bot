import telegram
import configparser
import logging

import pymongo
from util.mlab_util import JSONEncoder
from util.common import get_bot, get_db_conn, get_command, get_user_name
from util.num2chinese import num2chinese
from util.deck import Deck, Card, Hand
from util.logging import write_log_msg_to_db

import pytz
from datetime import datetime
import random, time
import pickle

bot = get_bot()

db_conn = get_db_conn()

# Load data from config.ini file
config = configparser.ConfigParser()
config.read('config/config.ini')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

action_map = {"":"",
              "raise" : "加注",
              "call" : "唔加",
              "fold": "唔玩"}

def format_poker_start_kb():
    custom_keyboard = [[telegram.InlineKeyboardButton(text="過大海啦", callback_data="pokerjoin"),
                        telegram.InlineKeyboardButton(text="買蛋卷算", callback_data="pokerquit")],
                       [telegram.InlineKeyboardButton(text="我準備好啦", callback_data="pokerready")]]
    
    reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
    return reply_markup

def format_poker_gaming_kb():
    custom_keyboard = [[telegram.InlineKeyboardButton(text="煲大佢", callback_data="pokerraise"),
                        telegram.InlineKeyboardButton(text="唔煲lu", callback_data="pokercall")],
                       [telegram.InlineKeyboardButton(text="玩唔起", callback_data="pokerfold"),
                        telegram.InlineKeyboardButton(text="我條底底呢", callback_data="pokeropen")]]
    
    reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
    return reply_markup
    
def format_poker_open_kb():
    custom_keyboard = [[telegram.InlineKeyboardButton(text="開第一張", callback_data="pokerfirst"),
                        telegram.InlineKeyboardButton(text="開尾果張", callback_data="pokerlast")],
                       [telegram.InlineKeyboardButton(text="我條底底呢", callback_data="pokeropen")]]
    reply_markup = telegram.InlineKeyboardMarkup(custom_keyboard)
    return reply_markup          

def format_message(doc):
    round_no = doc["round"]
    bet_amount = doc["bet"]
    current_bet = doc["currentBet"]
    
    bot_player = doc["botPlayer"]
    all_players = doc["players"]
    players = [all_players[player_id] for player_id in all_players if all_players[player_id]["playing"] != "rest"]
    playing_players = [all_players[player_id] for player_id in all_players if all_players[player_id]["playing"] == "play"]
    quit_players = [all_players[player_id] for player_id in all_players if all_players[player_id]["playing"] == "quit"]
    
    playing_players = playing_players + quit_players
    
    history = doc["history"]
    status = doc["status"]
    
    
    if (status != "end"):
        if status == "joining":
            text = "Poker - 第{}回 (<code>{}</code> 精兵 局)\n".format(num2chinese(round_no), bet_amount)
            text += "現況:\n"
            text += "莊 : <code>{}</code> 精兵 準備\n".format(bot_player["money"])
            for player in players:
                text += "{} : <code>{}</code> 精兵 {}\n".format(player["name"], player["money"], "準備" if player["playing"] == "ready" else "")
        elif status == "start" or status == "open":
            text = "Poker - 第{}回 (賭池 <code>{}</code> 精兵)\n".format(num2chinese(round_no), current_bet)
            text += "現況:\n"
            text += "莊 : <code>{}</code> 精兵 {}\n".format(bot_player["money"], action_map[bot_player["choice"]])
            text += show_cards(bot_player["cards"], bot_player["hidden"])
            for player in playing_players:
                text += "{} : <code>{}</code> 精兵 ({})\n".format(player["name"], player["money"], action_map[player["choice"]])
                text += show_cards(player["cards"], player["hidden"])
    else:
        max_player_money = max([all_players[player_id]["money"] for player_id in all_players])
        end_text = "創蛇!?" if bot_player["money"] >= max_player_money else "窮L"
        text = "完局:\n"
        text += "莊 : <code>{}</code> 精兵 {}\n".format(bot_player["money"], end_text)
        for player_id in all_players:
            end_text = "創蛇!?" if all_players[player_id]["money"] >= max_player_money and all_players[player_id]["money"] >= bot_player["money"] else "窮L"
            text += "{} : <code>{}</code> 精兵 {}\n".format(all_players[player_id]["name"], all_players[player_id]["money"], end_text)
            
    if history["round"] != 0:
        text += "===============\n"
        text += "上回提要:\n"
        bot_cards = history["botPlayer"]["finalCards"]
        
        text += "莊 : {} {} <code>{}</code> 精兵\n".format(Hand(bot_cards).get_chi_ranking(), "贏" if history["botPlayer"]["finalWinning"] > 0 else "賠", abs(history["botPlayer"]["finalWinning"]))
        text += show_cards(bot_cards, [])
        
        for player_id in history["players"]:
            player = history["players"][player_id]
            player_cards = player["finalCards"]

            text += "{} : {} {} <code>{}</code> 精兵 \n".format(all_players[player_id]["name"], Hand(player_cards).get_chi_ranking(), "贏" if player["finalWinning"] > 0 else "賠", abs(player["finalWinning"]))
            text += show_cards(player_cards, [])
    return text


async def render(chat_id, doc):
    try:
        text = format_message(doc)
        status = doc["status"]
        message_id = doc["messageId"]
        try:
            if status != "end":
                if status == "joining":
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=format_poker_start_kb(), parse_mode = "HTML")
                elif status == "open":
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=format_poker_open_kb(), parse_mode = "HTML")
                else:
                    await bot.edit_message_text(text, chat_id, message_id, reply_markup=format_poker_gaming_kb(), parse_mode = "HTML")
            else:
                await bot.edit_message_text(text, chat_id, message_id, parse_mode = "HTML")
        except Exception as e:
            write_log_msg_to_db(e)
    except Exception as ee:
        write_log_msg_to_db(ee)
        raise Exception()

async def handle_poker(update):
    chat_id = update.message.chat_id
    poker = db_conn.poker
    doc = poker.find_one({"chatId":chat_id})
    if doc is not None:
        doc = load(doc)
        if doc["status"] == "end":
                poker.delete_one({"chatId":chat_id})
                message = await bot.send_message(chat_id=chat_id, text="請等等，我繽紛樂緊")
                message_id = message.message_id
                poker.insert_one(new_game_doc(chat_id, message_id))
                doc = poker.find_one({"chatId":chat_id})
                doc = load(doc)
                await render(chat_id, doc)
        elif (update.message.text == "/poker clear"):
            poker.delete_one({"chatId":chat_id})
            try:
                await bot.delete_message(chat_id, doc["messageId"])
            except Exception as e:
                write_log_msg_to_db(e)
        else:
            try:
                await bot.delete_message(chat_id, doc["messageId"])
            except Exception as e:
                write_log_msg_to_db(e)
            message = await bot.send_message(chat_id=chat_id, text="請等等，我繽紛樂緊")
            message_id = message.message_id
            doc["messageId"] = message_id
            await render(chat_id, doc)
            save(doc)
    else:
        message = await bot.send_message(chat_id=chat_id, text="請等等，我繽紛樂緊")
        message_id = message.message_id
        poker.insert_one(new_game_doc(chat_id, message_id))
        doc = poker.find_one({"chatId":chat_id})
        doc = load(doc)
        await render(chat_id, doc)

async def callback_poker(update):
    query_id = update.callback_query.id
    text = ""
    show_alert = False
    
    data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    callback_user_id = str(update.callback_query.from_user.id)
    poker = db_conn.poker
    doc = poker.find_one({"chatId": chat_id})
    if doc == None:
        await bot.answer_callback_query(callback_query_id=update.callback_query.id, text="完左啦", show_alert=True)
        return
    doc = load(doc)
    bet_amount = doc["bet"]
    deck = doc["deck"]
    players = doc["players"]
    bot_player = doc["botPlayer"]
    turn = doc["turn"]
    
    
    if data == "pokerjoin":
        if callback_user_id not in players:
            doc["players"][callback_user_id] = new_player()
            user_name = get_user_name(update.callback_query.from_user)
            doc["players"][callback_user_id]["name"] = user_name
        elif callback_user_id in players and players[callback_user_id]["playing"] == "rest":
            doc["players"][callback_user_id]["playing"] = "join"
        else:
            show_alert = True
    if data == "pokerready":
        if callback_user_id in players and players[callback_user_id]["playing"] == "join":
            doc["players"][callback_user_id]["playing"] = "ready"
            ready_player = [players[player_id] for player_id in players if players[player_id]["playing"] == "ready"]
            join_player = [players[player_id] for player_id in players if players[player_id]["playing"] == "join"]
            if len(ready_player) > 0 and len(join_player) == 0:
                doc["status"] = "start"
                doc["turn"] = 2
                for player in ready_player:
                    player["playing"] = "play"
                    player["choice"] = ""
                    player["cards"] = [deck.draw_one(), deck.draw_one()]
                    player["hidden"] = [0]
                bot_player["cards"] = [deck.draw_one(), deck.draw_one()]
                bot_player["choice"] = decide_bot_action(doc)
                if bot_player["choice"] == "raise":
                    doc["currentBet"] += doc["bet"] // 2
                bot_player["hidden"] = [0]
                
        else:
            show_alert = True
    if data == "pokerquit":
        if callback_user_id in players and players[callback_user_id]["playing"] == "ready":
            text = "你準備左啦"
            show_alert = True
        elif callback_user_id in players and players[callback_user_id]["playing"] == "join":
            doc["players"][callback_user_id]["playing"] = "rest"
        else:
            show_alert = True
    if data == "pokerraise":
        if doc["status"] == "start":
            if callback_user_id in players and players[callback_user_id]["choice"] == "":
                players[callback_user_id]["choice"] = "raise"
                doc["currentBet"] += doc["bet"] // 2
            elif callback_user_id in players and players[callback_user_id]["choice"] != "":
                text = "你咪揀左囉"
                show_alert = True
            else:
                show_alert = True
        else:
            show_alert = True
    if data == "pokercall":
        if doc["status"] == "start":
            if callback_user_id in players and players[callback_user_id]["choice"] == "":
                players[callback_user_id]["choice"] = "call"
            elif callback_user_id in players and players[callback_user_id]["choice"] != "":
                text = "你咪揀左囉"
                show_alert = True
            else:
                show_alert = True
        else:
            show_alert = True
    if data == "pokerfold":
        if doc["status"] == "start":
            if callback_user_id in players and players[callback_user_id]["choice"] == "":
                players[callback_user_id]["choice"] = "fold"
                players[callback_user_id]["money"] -= doc["currentBet"]
                doc["foldBet"] += doc["currentBet"]
                if callback_user_id not in doc["history"]["players"]:
                    doc["history"]["players"][callback_user_id] = dict()
                doc["history"]["players"][callback_user_id]["winning"] = 0 - doc["currentBet"]
                doc["history"]["players"][callback_user_id]["cards"] = players[callback_user_id]["cards"]
                
            elif callback_user_id in players and players[callback_user_id]["choice"] != "":
                text = "你咪揀左囉"
                show_alert = True
            else:
                show_alert = True
        else:
            show_alert = True
    
    if data == "pokeropen":
        if doc["status"] == "start" or doc["status"] == "open":
            if callback_user_id in players and players[callback_user_id]["cards"] != [] and players[callback_user_id]["playing"] == "play":
                hand = Hand(players[callback_user_id]["cards"])
                
                text = "{}\n".format(hand.get_chi_ranking())
                text += show_cards(players[callback_user_id]["cards"], [])
                show_alert = True
            else:
                show_alert = True
                
    if data == "pokerfirst":
        if doc["status"] == "open":
            if callback_user_id in players and players[callback_user_id]["playing"] == "play" and len(players[callback_user_id]["hidden"]) == 2:
                players[callback_user_id]["hidden"] = [4]
            elif callback_user_id in players and players[callback_user_id]["playing"] == "play" and len(players[callback_user_id]["hidden"]) == 1:
                text = "你咪開左囉"
                show_alert = True
            else:
                show_alert = True
        else:
            show_alert = True
            
    if data == "pokerlast":
        if doc["status"] == "open":
            if callback_user_id in players and players[callback_user_id]["playing"] == "play" and len(players[callback_user_id]["hidden"]) == 2:
                players[callback_user_id]["hidden"] = [0]
            elif callback_user_id in players and players[callback_user_id]["playing"] == "play" and len(players[callback_user_id]["hidden"]) == 1:
                text = "你咪開左囉"
                show_alert = True
            else:
                show_alert = True
        else:
            show_alert = True
    
    not_yet_choose_player = [players[player_id] for player_id in players if players[player_id]["playing"] == "play" and players[player_id]["choice"] == ""]
    not_yet_open_player = [players[player_id] for player_id in players if players[player_id]["playing"] == "play" and len(players[player_id]["hidden"]) == 2]
    
    if (doc["status"] == "start" and doc["turn"] != 5 and len(not_yet_choose_player) == 0):
        playing_players = [players[player_id] for player_id in players if players[player_id]["playing"] == "play"]
        doc["turn"] += 1
        not_fold_players = [player for player in playing_players if player["choice"] != "fold"]
        if len(not_fold_players) == 0:
            doc = check_win(doc)
        else:
            for player in playing_players:
                if player["choice"] != "fold":
                    player["cards"].append(deck.draw_one())
                    player["choice"] = ""
                    if doc["turn"] == 5:
                        player["hidden"].append(4)
                        doc["status"] = "open"
                else:
                    player["playing"] = "quit"
            bot_player["cards"].append(deck.draw_one())
            bot_player["choice"] = decide_bot_action(doc)
            if bot_player["choice"] == "raise":
                doc["currentBet"] += doc["bet"] // 2
            if doc["turn"] == 5:
                bot_player["hidden"] = decide_bot_open(bot_player["cards"])
        
    elif (doc["status"] == "start" and doc["turn"] == 5 and len(not_yet_choose_player) == 0):
        playing_players = [players[player_id] for player_id in players if players[player_id]["playing"] == "play"]
        doc = check_win(doc)
    elif (doc["status"] == "open" and len(not_yet_open_player) == 0):
        doc["status"] = "start"

    await answer_query(query_id, text, show_alert)
    await render(chat_id, doc)
    save(doc)

def new_game_doc(chat_id, message_id):
    deck = Deck(symbol=True)
    bot_player = new_player()
    base_bet = 10

    doc =  {"round": 1,
            "bet": base_bet,
            "currentBet": base_bet, 
            "foldBet": 0,
            "turn": 0,
            "messageId": message_id,
            "chatId": chat_id,
            "status": "joining",
            "deck": pickle.dumps(deck),
            "botPlayer": {"cards": bot_player["cards"],
                          "money": bot_player["money"],
                          "hidden": bot_player["hidden"],
                          "choice": ""
                         },
            "players": dict(), 
            "history": {"round": 0,
                        "botPlayer": dict(),
                        "players": dict()}}

    return doc

def show_cards(cards, hidden):
    cards_text = []
    for index in range(len(cards)):
        if index in hidden:
            cards_text.append("？")
        else:
            cards_text.append(str(cards[index]))

    return " ".join(cards_text) + "\n"

def decide_bot_action(doc):
    bot_player = doc["botPlayer"]
    players = doc["players"]
    
    playing_not_fold_players = [player_id for player_id in players if players[player_id]["playing"] == "play" and players[player_id]["choice"] != "fold"]
    bot_player_wins = sum([Hand(bot_player["cards"]).compare(Hand(players[player_id]["cards"]), count_suit=True) for player_id in playing_not_fold_players])

    if bot_player_wins >= len(playing_not_fold_players) / 2:
        return "raise"    
    return "call"
    
def decide_bot_open(cards):
    result = Hand(cards[0:4]).compare(Hand(cards[1:5]), count_suit=True)
    if result >= 0:
        return [0]
    else:
        return [4]
        
def check_win(doc):
    bot_player = doc["botPlayer"]
    players = doc["players"]
    
    
    playing_not_fold_players = [player_id for player_id in players if players[player_id]["playing"] == "play" and players[player_id]["choice"] != "fold"]
    bot_player_wins = sum([Hand(bot_player["cards"]).compare(Hand(players[player_id]["cards"]), count_suit=True) for player_id in playing_not_fold_players])
    winner_wins = bot_player_wins
    winner = "bot"
    
    for selected_player_id in playing_not_fold_players:
        
        player_wins = sum([Hand(players[selected_player_id]["cards"]).compare(Hand(players[player_id]["cards"]), count_suit=True) for player_id in playing_not_fold_players if player_id != selected_player_id] + [Hand(players[selected_player_id]["cards"]).compare(Hand(bot_player["cards"]), count_suit=True)])
        if player_wins > winner_wins:
            winner_wins = player_wins
            winner = selected_player_id
    
    
    total_win_bet = doc["foldBet"]
    
    for player_id in playing_not_fold_players:
        if player_id != winner:
            players[player_id]["money"] -= doc["currentBet"]
            doc["history"]["players"][player_id] = dict()
            doc["history"]["players"][player_id]["cards"] = players[player_id]["cards"]
            doc["history"]["players"][player_id]["winning"] = 0 - doc["currentBet"]

            total_win_bet += doc["currentBet"]
    
    
    doc["history"]["botPlayer"]["cards"] = bot_player["cards"]
    if winner == "bot":
        bot_player["money"] += total_win_bet
        doc["history"]["botPlayer"]["winning"] = total_win_bet
    else:
        bot_player["money"] -= doc["currentBet"]
        doc["history"]["botPlayer"]["winning"] = 0 - doc["currentBet"]
        
        total_win_bet += doc["currentBet"]
        players[winner]["money"] += total_win_bet
        doc["history"]["players"][winner] = dict()
        doc["history"]["players"][winner]["cards"] = players[winner]["cards"]
        doc["history"]["players"][winner]["winning"] = total_win_bet

    doc["history"]["round"] = doc["round"]    
    for player_id in doc["history"]["players"]:
        doc["history"]["players"][player_id]["finalCards"] = doc["history"]["players"][player_id]["cards"]
        doc["history"]["players"][player_id]["finalWinning"] = doc["history"]["players"][player_id]["winning"]
    doc["history"]["botPlayer"]["finalCards"] = doc["history"]["botPlayer"]["cards"]
    doc["history"]["botPlayer"]["finalWinning"] = doc["history"]["botPlayer"]["winning"]

    
    doc["round"] += 1
    doc["status"] = "joining"
    for player_id in players:
        player = players[player_id]
        if player["money"] <= 0 or bot_player["money"] <= 0:
            doc["status"] = "end"
            break
        player["choice"] = ""
        player["cards"] = []
        player["playing"] = "join"
        player["hidden"] = []
        
    doc["deck"] = Deck(symbol=True)
    doc["bet"] = doc["bet"] + 10
    doc["currentBet"] = doc["bet"]
    doc["foldBet"] = 0
    doc["turn"] =  0

    return doc

def new_player():
    player = dict()
    player["cards"] = []
    player["money"] = 10000
    player["playing"] = "join"
    player["hidden"] = []
    player["choice"] = ""
    return player

def load(doc):
    doc["deck"] = pickle.loads(doc["deck"])
    if doc["botPlayer"]["cards"] != []:
        doc["botPlayer"]["cards"] = pickle.loads(doc["botPlayer"]["cards"])
    for player_id in doc["players"]:
        if doc["players"][player_id]["cards"] != []:
            doc["players"][player_id]["cards"] = pickle.loads(doc["players"][player_id]["cards"])
    if doc["history"]["round"] != 0:
        doc["history"]["botPlayer"]["cards"] = pickle.loads(doc["history"]["botPlayer"]["cards"])
        doc["history"]["botPlayer"]["finalCards"] = pickle.loads(doc["history"]["botPlayer"]["finalCards"])
        for player_id in doc["history"]["players"]:
            doc["history"]["players"][player_id]["cards"] = pickle.loads(doc["history"]["players"][player_id]["cards"])
            doc["history"]["players"][player_id]["finalCards"] = pickle.loads(doc["history"]["players"][player_id]["finalCards"])
    return doc


def save(doc):
    doc["deck"] = pickle.dumps(doc["deck"])
    doc["botPlayer"]["cards"] = pickle.dumps(doc["botPlayer"]["cards"])
    for player_id in doc["players"]:
        doc["players"][player_id]["cards"] = pickle.dumps(doc["players"][player_id]["cards"])
    if doc["history"]["round"] != 0:
        doc["history"]["botPlayer"]["cards"] = pickle.dumps(doc["history"]["botPlayer"]["cards"])
        doc["history"]["botPlayer"]["finalCards"] = pickle.dumps(doc["history"]["botPlayer"]["finalCards"])
        for player_id in doc["history"]["players"]:
            doc["history"]["players"][player_id]["cards"] = pickle.dumps(doc["history"]["players"][player_id]["cards"])
            doc["history"]["players"][player_id]["finalCards"] = pickle.dumps(doc["history"]["players"][player_id]["finalCards"])
    db_conn.poker.replace_one({'_id': doc['_id']}, doc, upsert=True)
    
async def answer_query(id, text="", show_alert=False):
    if text == "" and not show_alert:
        await bot.answer_callback_query(callback_query_id=id)
    elif text == "" and show_alert:
        await bot.answer_callback_query(callback_query_id=id, text="咪亂玩", show_alert=True)
    else:
        await bot.answer_callback_query(callback_query_id=id, text=text, show_alert=True)

