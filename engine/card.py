# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    card.py                                            :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: alechin <alechin@student.42kl.edu.my>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/14 13:58:25 by alechin           #+#    #+#              #
#    Updated: 2026/09/14 13:58:25 by alechin          ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import random
# from engine import moneyManipulate

# ------------------------
# CARDS
# ------------------------

# REMINDER - FILL [x] with ACTUAL PROPERTY

chanceCards = [
	{ "id": "c_adv",    "text": "Advance to Mayfair", "action": "moveTo", "position": 40 },
	{ "id": "c_go",    "text": "Advance to Go (Collect M200)", "action": "moveTo", "position": 0 },
	{ "id": "c_back3", "text": "Go back 3 spaces",             "action": "moveBy", "steps": -3 },
	{ "id": "c_tax",   "text": "Pay a poor tax of M15",        "action": "pay",    "amount": 15 },
	{ "id": "c_jail",  "text": "Go to jail.",                  "action": "goToJail" },
	{ "id": "c_free",  "text": "Get out of jail free",         "action": "jailCard" }
]

chanceCardsDiscarded = []

communityChestCards = [
	{ "id": "cc_bank", "text": "Bank error in your favor! Collect M200", "action": "collect", "amount": 200 },
	{ "id": "cc_bday", "text": "It's yo birthday! Collect M10 from each player", "action": "collectFromEach", "amount": 10 }
]

communityChestCardsDiscarded = []


def drawChanceCard():
	if chanceCards.len() == 0:
		chanceCards = chanceCardsDiscarded
		chanceCardsDiscarded = []
		random.shuffle(chanceCards)
	card = chanceCards.pop()
	chanceCardsDiscarded.append(card)
	return card

def drawCommunityChestCard():
	if communityChestCards.len() == 0:
			communityChestCards = communityChestCardsDiscarded
			communityChestCardsDiscarded = []
			random.shuffle(communityChestCards)
	card = communityChestCards.pop()
	communityChestCardsDiscarded.append(card)
	return card

def doCollect(game, player, card):
	game.gainMoney(player.playerId, card["amount"])

def doPay(game, player, card):
	game.painMoney(player.playerId, card["amount"])

def doCollectFromEach(game, player, card):
	for p in game.players:
		if p.playerId != player.playerId and not p.bankrupt:
			game.transferMoney(p.playerId, player.playerId, card["amount"])

def doMoveTo(game, player, card):
	steps = (card["position"] - player.position) % len(game.board)
	return game.movePlayer(player, steps)

def doMoveBy(game, player, card):
	return game.movePlayer(player, card["steps"])

def doGoToJail(game, player, card):
	game.sendToJail(player.playerId)

def doJailCard(game, player, card):
	player.getOutOfJailCards += 1

CARD_ACTIONS = {
	"collect": doCollect,
	"pay": doPay,
	"collectFromEach": doCollectFromEach,
	"moveTo": doMoveTo,
	"moveBy": doMoveBy,
	"goToJail": doGoToJail,
	"jailCard": doJailCard,
}

def applyCardEffects(card, player, game):
	cardAction = CARD_ACTIONS.get(card["action"])
	if cardAction is None:
		return {"type": "error", "message": f"Unknown card action {card['action']}"}
	return cardAction(game, player, card)

# old way is  too unstable and is hard to implement new shit

# def applyCardEffects(card, player, Game):
# 	if "It's your birthday" in card:
# 		giftSum = 0
# 		for p in Game.players:
# 			if p.playerId != player.playerId:
# 				Game.painMoney(p.playerId, 10)
# 				giftSum += 10
# 		Game.gainMoney(player.playerId, giftSum)
# 	elif "Collect" in card:
# 		amount = (card.split('M')[1] if 'M' in card else 0)
# 		if (len(amount) > 1):
# 			int(amount[:-1])
# 		player.money += amount
# 	elif "Pay" in card:
# 		amount = int(card.split('M')[1] if 'M' in card else 0)
# 		player.money -= amount
# 	elif "Go to jail" in card:
# 		Game.sendToJail(player, player.Id)
# 	elif "Get out of jail free" in card:
# 		player.getOutOfJailCards += 1
# 	elif "You inherit M100" in card:
# 		Game.gainMoney(player.playerId, 100)