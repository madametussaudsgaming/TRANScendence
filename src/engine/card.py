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
from engine import Game
from moneyManipulation import moneyManipulate

# ------------------------
# CARDS
# ------------------------

# REMINDER - FILL [x] with ACTUAL PROPERTY

chanceCards = [
	"Advance to Go (Collect M200)",
	"Go back 3 spaces",
	"Advance to [x]",
	"Pay a poor tax of M15",
	"Take a ride on the [x]",
	"Advance to [x]",
	"Get out of jail free",
	"Go to jail."
]

communityChestCards = [
	"Advance to Go (Collect M200)",
	"Bank error in your favor!. Collect (M200)",
	"Doctor's fees. Pay M50",
	"Get out of jail free",
	"Go to jail.",
	"It's your birthday! Collect M10 from each player",
	"Pay hospital fees of M200",
	"You inherit M100"
]

def drawChanceCard():
	random.shuffle(chanceCards)
	return chanceCards.pop()

def drawCommunityChestCard():
	random.shuffle(communityChestCards)
	return communityChestCards.pop()

def applyCardEffects(card, player):
	if "Collect" in card:
		amount = int(card.split('$')[1] if '$' in card else 0)
		player.money += amount
	elif "Pay" in card:
		amount = int(card.split('$')[1] if '$' in card else 0)
		player.money -= amount
	elif "Go to jail" in card:
		player.inJail = True
	elif "It's your birthday" in card:
		giftSum = 0
		for p in Game.players:
			if p.playerId != player.playerId:
				moneyManipulate.painMoney(p.playerId, 10)
				giftSum += 10
		moneyManipulate.gainMoney(player.playerId, giftSum)