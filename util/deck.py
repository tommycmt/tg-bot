import random

suits = ["d", "c", "h", "s"]
ranks = ["2","3","4","5","6","7","8","9","T","J","Q","K", "A"]
hand_ranking=["high_card", "one_pair", "two_pair", "three_of_a_kind", "straight", "flush", "full_house", "four_of_a_kind", "straight_flush"]

hand_ranking_chi = {"high_card": "單條",
                    "one_pair": "啤",
                    "two_pair": "對啤",
                    "three_of_a_kind": "三條",
                    "straight": "順",
                    "flush": "花",
                    "full_house": "葫蘆",
                    "four_of_a_kind": "四條",
                    "striaght_flush": "同花順"}
                    

suits_symbol = {"d": "\U00002666",
                "c": "\U00002663",
                "h": "\U00002665",
                "s": "\U00002660",
                "r": "紅色",
                "b": "黑色"}

suits_name = {"d": "階磚",
              "c": "梅花",
              "h": "紅心",
              "s": "葵扇",
              "r": "紅色",
              "b": "黑色"}
joker_symbol = "\U0001F0CF"
joker_name = "G"

default_rank_order=["2","3","4","5","6","7","8","9","T","J","Q","K","A"]
default_suit_order=["d", "c", "h", "s"]
default_straight_order=["A","2","3","4","5","6","7","8","9","T","J","Q","K","A"]



class Deck():
    def __init__(self, joker=False, symbol=False):
        self.cards = []
        if symbol:
            self.suits_repr = suits_symbol
            self.joker_repr = joker_symbol
        else:
            self.suits_repr = suits_name
            self.joker_repr = joker_name
        for suit in suits:
            for rank in ranks:
                self.cards.append(Card(rank, suit, self.suits_repr, self.joker_repr))
        if joker:
            self.cards.append(Card("G", "r", self.suits_repr, self.joker_repr))
            self.cards.append(Card("G", "b", self.suits_repr, self.joker_repr))

    def draw_one(self):
        card = random.choice(self.cards)
        self.cards.remove(card)
        return card

    def put_one_back(self, card):
        if type(card) == Card:
            self.cards.append(card)
        else:
            raise Exception("Type Mismatch")

    def shuffle(self):
        random.shuffle(self.cards)
        
    def __str__(self):
        return str(self.cards)
        

class Card():
    def __init__(self, rank, suit, suits_repr=suits_symbol, joker_repr=joker_symbol):
        self.rank = rank
        self.suit = suit
        self.suits_repr = suits_repr
        self.joker_repr = joker_repr

    def compare(self, other, rank_order=default_rank_order,
                suit_order=default_suit_order, straight_order=default_straight_order, count_suit=False):
        if isinstance(other, self.__class__):
            hand1 = Hand(self.cards())
            hand2 = Hand(other.cards())
            return hand1.compare(hand2, rank_order=rank_order, suit_order=suit_order, straight_order=straight_order)
        else:
            raise Exception("Uncomparable")
                            
    def __repr__(self):
        return str(self.rank+self.suit)
    
    def __str__(self):
        if self.rank == "G":
            return str(self.suits_repr[self.suit]) + str(self.joker_repr)
        return str(self.rank) + str(self.suits_repr[self.suit])

class Hand():
    
    def __init__(self, cards):
        self.cards = cards

    def compare(self, other, rank_order=default_rank_order,
                suit_order = default_suit_order, straight_order=default_straight_order, count_suit=False):
        if isinstance(other, self.__class__):
            if len(self.cards) == len(other.cards):
                self_rank = self.get_ranking(straight_order)
                other_rank = other.get_ranking(straight_order)
                if hand_ranking.index(self_rank) > hand_ranking.index(other_rank):
                    return 1
                elif hand_ranking.index(self_rank) < hand_ranking.index(other_rank):
                    return -1
                else:
                    return Hand.compare_same_ranking(self, other, self_rank, rank_order, suit_order, count_suit=count_suit)
            else:
                raise Exception("Cards number in hand are not the same")
        else:
            raise Exception("Uncomparable")

    @staticmethod
    def compare_same_ranking(h1, h2, rank, rank_order, suit_order, count_suit):
        if not count_suit:
            if rank in ["high_card", "straight", "flush", "straight_flush"]:
                sorted_h1 = sorted([card for card in h1.cards],key=lambda x:rank_order.index(x.rank)*4+suit_order.index(x.suit), reverse=True)
                sorted_h2 = sorted([card for card in h2.cards],key=lambda x:rank_order.index(x.rank)*4+suit_order.index(x.suit), reverse=True)
                for index in range(len(h1.cards)):
                    if rank_order.index(sorted_h1[index].rank) > rank_order.index(sorted_h2[index].rank):
                        return 1
                    elif rank_order.index(sorted_h1[index].rank) < rank_order.index(sorted_h2[index].rank):
                        return -1
                return 0
            if rank in ["one_pair", "two_pair", "three_of_a_kind", "full_house", "four_of_a_kind"]:
                h1_count_dict = Hand.count_number_of_same_rank(h1)
                h2_count_dict = Hand.count_number_of_same_rank(h2)
                h1_order_list = sorted(h1_count_dict, key=lambda k: (h1_count_dict[k],rank_order.index(k)), reverse=True)
                h2_order_list = sorted(h2_count_dict, key=lambda k: (h2_count_dict[k],rank_order.index(k)), reverse=True)
                h1_order_list = [rank for rank in h1_order_list for ele in range(h1_count_dict[rank])]
                h2_order_list = [rank for rank in h2_order_list for ele in range(h2_count_dict[rank])]
                for index in range(len(h1.cards)):
                    if rank_order.index(h1_order_list[index]) > rank_order.index(h2_order_list[index]):
                        return 1
                    elif rank_order.index(h1_order_list[index]) < rank_order.index(h2_order_list[index]):
                        return -1
                return 0
        else:
            if rank == "high_card":
                sorted_h1 = sorted([card for card in h1.cards],key=lambda x:rank_order.index(x.rank)*4+suit_order.index(x.suit), reverse=True)
                sorted_h2 = sorted([card for card in h2.cards],key=lambda x:rank_order.index(x.rank)*4+suit_order.index(x.suit), reverse=True)
                for index in range(len(h1.cards)):
                    if rank_order.index(sorted_h1[index].rank) > rank_order.index(sorted_h2[index].rank):
                        return 1
                    elif rank_order.index(sorted_h1[index].rank) < rank_order.index(sorted_h2[index].rank):
                        return -1
                    if suit_order.index(sorted_h1[index].suit) > suit_order.index(sorted_h2[index].suit):
                        return 1
                    elif suit_order.index(sorted_h1[index].suit) < suit_order.index(sorted_h2[index].suit):
                        return -1
                return 0
            if rank in ["straight", "flush", "straight_flush"]:
                sorted_h1 = sorted([card for card in h1.cards],key=lambda x:rank_order.index(x.rank)*4+suit_order.index(x.suit), reverse=True)
                sorted_h2 = sorted([card for card in h2.cards],key=lambda x:rank_order.index(x.rank)*4+suit_order.index(x.suit), reverse=True)
                for index in range(len(h1.cards)):
                    if rank_order.index(sorted_h1[index].rank) > rank_order.index(sorted_h2[index].rank):
                        return 1
                    elif rank_order.index(sorted_h1[index].rank) < rank_order.index(sorted_h2[index].rank):
                        return -1
                for index in range(len(h1.cards)):
                    if suit_order.index(sorted_h1[index].suit) > suit_order.index(sorted_h2[index].suit):
                        return 1
                    elif suit_order.index(sorted_h1[index].suit) < suit_order.index(sorted_h2[index].suit):
                        return -1
                return 0
            if rank in ["one_pair", "two_pair", "three_of_a_kind", "full_house", "four_of_a_kind"]:
                h1_count_dict = Hand.count_number_of_same_rank(h1)
                h2_count_dict = Hand.count_number_of_same_rank(h2)
                h1_order_list = sorted(h1_count_dict, key=lambda k: (h1_count_dict[k],rank_order.index(k)), reverse=True)
                h2_order_list = sorted(h2_count_dict, key=lambda k: (h2_count_dict[k],rank_order.index(k)), reverse=True)
                h1_order_list = [rank for rank in h1_order_list for ele in range(h1_count_dict[rank])]
                h2_order_list = [rank for rank in h2_order_list for ele in range(h2_count_dict[rank])]
                for index in range(len(h1.cards)):
                    if rank_order.index(h1_order_list[index]) > rank_order.index(h2_order_list[index]):
                        return 1
                    elif rank_order.index(h1_order_list[index]) < rank_order.index(h2_order_list[index]):
                        return -1
                sorted_h1 = sorted([card for card in h1.cards],key=lambda x:rank_order.index(x.rank)*4+suit_order.index(x.suit), reverse=True)
                sorted_h2 = sorted([card for card in h2.cards],key=lambda x:rank_order.index(x.rank)*4+suit_order.index(x.suit), reverse=True)
                for index in range(len(h1.cards)):
                    if suit_order.index(sorted_h1[index].suit) > suit_order.index(sorted_h2[index].suit):
                        return 1
                    elif suit_order.index(sorted_h1[index].suit) < suit_order.index(sorted_h2[index].suit):
                        return -1
                return 0
        raise Exception("Unknown Ranking")
    
    @staticmethod
    def count_number_of_same_rank(h):
        count = 0
        count_dict = dict()
        for card in h.cards:
            if card.rank not in count_dict:
                count_dict.update({card.rank: 1})
            else:
                count_dict.update({card.rank: count_dict[card.rank] + 1})
        return count_dict
    
    def get_ranking(self, straight_order=default_straight_order):
        possible_ranking = []
        if self.is_straight_flush(straight_order):
            possible_ranking.append("straight_flush")
        if self.is_four_of_a_kind():
            possible_ranking.append("four_of_a_kind")
        if self.is_full_house():
            possible_ranking.append("full_house")
        if self.is_flush():
            possible_ranking.append("flush")
        if self.is_straight(straight_order):
            possible_ranking.append("straight")
        if self.is_three_of_a_kind():
            possible_ranking.append("three_of_a_kind")
        if self.is_two_pair():
            possible_ranking.append("two_pair")
        if self.is_one_pair():
            possible_ranking.append("one_pair")
        if len(possible_ranking) == 0:
            return "high_card"
        else:
            return hand_ranking[max([hand_ranking.index(rank) for rank in possible_ranking])]
    
    def get_chi_ranking(self, rank_order=default_rank_order, suit_order =default_suit_order, straight_order=default_straight_order):
        rank = self.get_ranking(straight_order)
        if rank in ["high_card", "straight", "flush", "straight_flush"]:
            sorted_hand = sorted([card for card in self.cards],key=lambda x:rank_order.index(x.rank)*4+suit_order.index(x.suit), reverse=True)
            prefix = str(sorted_hand[0].rank)
            if rank != "high_card":
                prefix += " " + str(sorted_hand[1].rank)
        else:
            count_dict = Hand.count_number_of_same_rank(self)
            order_list = sorted(count_dict, key=lambda k: (count_dict[k],rank_order.index(k)), reverse=True)
            prefix = str(order_list[0])
            if rank != "one_pair":
                prefix += " " + str(order_list[1])
        return  hand_ranking_chi[rank] + " " + prefix
    


    def is_straight_flush(self, straight_order):
        if len(self.cards) != 5:
            return False
        return self.is_straight(straight_order) and self.is_flush()

    def is_four_of_a_kind(self):
        if len(self.cards) < 4:
            return False
        count_dict = Hand.count_number_of_same_rank(self)
        if max(count_dict.values()) == 4:
            return True
        return False
    
    def is_full_house(self):
        if len(self.cards) != 5:
            return False
        count_dict = Hand.count_number_of_same_rank(self)
        if max(count_dict.values()) == 3:
            three_card_rank = max(count_dict,key=lambda k: count_dict[k])
            count_dict.pop(three_card_rank)
            if max(count_dict.values()) == 2:
                return True
            return False
        return False
    
    def is_flush(self):
        if len(self.cards) != 5:
            return False
        if len(set([card.suit for card in self.cards])) == 1:
            return True
        return False

    def is_straight(self, straight_order):
        if len(self.cards) != 5:
            return False
        l1 = sorted([card.rank for card in self.cards],key=lambda x:straight_order[0:-1].index(x))
        l2 = sorted([card.rank for card in self.cards],key=lambda x:straight_order[1:].index(x))
        index_1 = 0
        index_2 = 0
        for rank in straight_order:
            if rank == l1[index_1]:
                index_1 += 1
            else:
                index_1 = 0
            if rank == l2[index_2]:
                index_2 += 1
            else:
                index_2 = 0
            if index_1 == 5 or index_2 == 5:
                return True
        return False

    def is_three_of_a_kind(self):
        if len(self.cards) < 3:
            return False
        count_dict = Hand.count_number_of_same_rank(self)
        if max(count_dict.values()) == 3:
            return True
        return False
    
    def is_two_pair(self):
        if len(self.cards) < 4:
            return False
        count_dict = Hand.count_number_of_same_rank(self)
        if max(count_dict.values()) == 2:
            pair_card_rank = max(count_dict,key=lambda k: count_dict[k])
            count_dict.pop(pair_card_rank)
            if max(count_dict.values()) == 2:
                return True
            return False
        return False
    
    def is_one_pair(self):
        if len(self.cards) < 2:
            return False
        count_dict = Hand.count_number_of_same_rank(self)
        if max(count_dict.values()) == 2:
            return True
        return False
    
    def __str__(self):
        return str(self.cards)
