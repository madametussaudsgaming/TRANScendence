# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    engine.py                                          :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: rpadasia <ryanpadasian@gmail.com>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/14 14:28:44 by alechin           #+#    #+#              #
#    Updated: 2026/11/08 18:33:01 by rpadasia         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import random
import card

from tile import (
	PropertyTile,
	RailroadTile,
	UtilityTile,
	TaxTile,
	ChanceTile,
	CommunityChestTile,
	GoTile,
	JailTile,
	FreeParkingTile,
	GoToJailTime,
)

ACTIONS = {
	"roll":        "rollNMove",
	"buy":         "buyProperty",
	"decline":     "declinePurchase",
	"endTurn":     "endTurn",
	"mortgage":    "mortgage",
	"build":       "buildHouse",
	"jailPay":     "payJailFine",
	"jailCard":    "useJailCard",
	"bid":         "placeBid",
	"passAuction": "passAuction",
	"sellHouse":   "sellHouse",
	"bankrupt":    "declareBankruptcy",
	}

JAIL_POSITION = 10
JAIL_FINE = 50
MAX_JAIL_TURNS = 3
MAX_DOUBLES = 3
PASS_GO_YEEHAW = 200

class GameError(Exception):
    pass


# ----------------------
# PLAYER
# ----------------------

class Player:
	def __init__(self, playerId, name):
		self.playerId = playerId
		self.name = name
		self.position = 0
		self.money = 1500
		self.properties = []
		self.inJail = False
		self.jailTurns = 0
		self.getOutOfJailCards = 0
		self.bankrupt = False

class PreGame:
	# while in lobby
	# when receive enter button, take user credentials and username (protect from sql injection), make a temp player, add to an array
	# when every player currently joined presses 'ready' OR 4 players have been reached, then a countdown of 10 seconds happens then the game starts.
	#if a player disconnects during this time, then everyone's no longer ready. if somebody clicks the button again (un-ready) everyone is no longer ready
	def __init__(self):
		self.players = []
		self.readyPlayers = set()
		self.started = False

	def	getTempPlayer(self, ID):
		for p in self.players:
			if p.playerId == ID:
				return p
		print ("[DEBUG] Player Not Found")
		return None

	def tempPlayerJoin(self, ID, username):
		if self.started:
			return False
		if len(self.players) >= 4:
			return False
		if self.getTempPlayer(ID) is not None:
			return False
		self.players.append(Player(ID, username))
		return True

	def tempPlayerLeft(self, ID):
		target = self.getTempPlayer(ID)
		if target is None:
			return False
		self.players.remove(target)
		self.readyPlayers.clear()
		return True

	def setReady(self, ID):
		player = self.getTempPlayer(ID)
		if player is None:
			return False
		if ID in self.readyPlayers:
			self.readyPlayers.remove(ID)
		else:
			self.readyPlayers.add(ID)
		return True

	def allPlayerReady(self):
		if len(self.players) == 0:
			return False
		return len(self.readyPlayers) == len(self.players)

	def canStart(self):
		if len(self.players) < 2 or len(self.players) > 4:
			return False
		if len(self.players) == 4:
			return True
		return self.allPlayerReady()

	def startGame(self):
		if not self.canStart():
			return None
		self.started = True
		return self.players

	#ONCE REACHED WE"RE USING WEBSOCKETS, leaveGame and startGame on the website side
	#we need to create an array of Player(class) by the time preGame ends to give to Game

# ----------------------
# GAME
# ----------------------

class Game:
	def __init__(self, board, players):
		self.board = board
		self.players = players
		self.currentTurnIndex = 0
		self.doubleStreak = 0
		self.hasRolled = False
		self.pendingAction = None
		self.gameOver = False
		self.winnerId = None
		self.auctionState = None
		self.tradeOffers = {}
		self.nextTradeId = 1
		self.chanceDeck = card.newDeck(card.CHANCE_CARDS)
		self.communityDeck = card.newDeck(card.COMMUNITY_CHEST_CARDS)
		self.chanceDiscard = []
		self.communityDiscard = []
		# debts waiting for pendingAction to be free, e.g. several players owing at once from a card
		self.debtQueue = []


	def buyProperty(self, playerId, position):
		player = self.getPlayer(playerId)
		if player is None:
			return False
		# check that pendingAction matches THIS player and position
		if self.pendingAction != {"type": "purchase", "playerId": playerId, "position": position}: return False
		if position < 0 or position >= len(self.board):
			return False
		tile = self.board[position]
		if not hasattr(tile, "price"):
			return False
		if tile.owner is not None:
			return False
		if player.money < tile.price:
			return False
		player.money -= tile.price
		tile.owner = player
		player.properties.append(position)
		self.pendingAction = None
		self.promoteQueuedDebt()
		return True

	def declinePurchase(self, playerId):
		action = self.pendingAction
		if action is None:
			return False
		if action["type"] != "purchase":
			return False
		if action["playerId"] != playerId:
			return False
		position = action["position"]
		return self.auction(position, playerId)

	def mortgage(self, playerId, position):
		player = self.getPlayer(playerId)
		if player is None:
			return False
		if position < 0 or position >= len(self.board):
			return False
		tile = self.board[position]
		if not hasattr(tile, "owner"):
			return False
		if tile.owner != player:
			return False
		if tile.mortgaged:
			return False
		if hasattr(tile, "houses") and tile.houses > 0:
			return False
		player.money += tile.mortgageValue
		tile.mortgaged = True
		# only a debt can be paid off here, auctions have no playerId
		if self.pendingAction is not None and self.pendingAction["type"] == "debt":
			if self.pendingAction["playerId"] == playerId:
				self.resolveDebt(playerId)
		return True

	def auction(self, position, initiatorId):
		action = self.pendingAction

		if action is not None:
			if action["type"] != "purchase":
				return False
			if action["position"] != position:
				return False
		if position < 0 or position >= len(self.board):
			return False
		tile = self.board[position]
		if not isinstance(tile, (PropertyTile, RailroadTile, UtilityTile)):
			return False
		if tile.owner is not None:
			return False
		activeBidders = [
			p.playerId for p in self.players
			if not p.bankrupt
		]
		if len(activeBidders) < 2:
			return False

		if initiatorId in activeBidders:
			activeBidders.remove(initiatorId)
			activeBidders.insert(0, initiatorId)
		self.auctionState = {
			"position": position,
			"currentBid": 0,
			"highestBidder": None,
			"activeBidders": activeBidders
		}
		self.pendingAction = {
			"type": "auction",
			"position": position
		}
		return {
			"type": "auction_started",
			"position": position,
			"name": tile.name,
			"currentBid": 0,
			"currentBidder": activeBidders[0]
		}

	def placeBid(self, playerId, amount):
		state = self.auctionState

		if state is None:
			return False
		if not state["activeBidders"]:
			return False
		if state["activeBidders"][0] != playerId:
			return False
		player = self.getPlayer(playerId)

		if player is None or player.bankrupt:
			return False
		if amount <= state["currentBid"]:
			return False
		if amount > player.money:
			return False
		state["currentBid"] = amount
		state["highestBidder"] = playerId
		if len(state["activeBidders"]) == 1:
			return self.finishAuction()
		state["activeBidders"].append(state["activeBidders"].pop(0))
		return {
			"type": "bid_placed",
			"playerId": playerId,
			"amount": amount,
			"currentBidder": state["activeBidders"][0]
		}

	def passAuction(self, playerId):
		state = self.auctionState

		if state is None:
			return False
		if not state["activeBidders"]:
			return False
		if state["activeBidders"][0] != playerId:
			return False
		state["activeBidders"].pop(0)
		if len(state["activeBidders"]) == 0:
			return self.finishAuction()
		if len(state["activeBidders"]) == 1 and state["activeBidders"][0] == state["highestBidder"]:
			return self.finishAuction()
		return {
			"type": "player_passed",
			"playerId": playerId,
			"currentBidder": state["activeBidders"][0]
		}

	def finishAuction(self):
		state = self.auctionState

		if state is None:
			return False
		position = state["position"]
		tile = self.board[position]
		winnerId = state["highestBidder"]
		winnerBid = state["currentBid"]

		if winnerId is None:
			result = {
				"type": "auction_ended",
				"winnerId": None,
				"message": "Nobody placed a bid"
			}
		else:
			winner = self.getPlayer(winnerId)

			if winner is None or winner.bankrupt:
				return False
			if winner.money < winnerBid or tile.owner is not None:
				return False
			winner.money -= winnerBid
			winner.properties.append(position)
			tile.owner = winner
			result = {
				"type": "auction_ended",
				"winnerId": winnerId,
				"winningBid": winnerBid,
				"position": position,
				"name": tile.name
			}
		self.auctionState = None
		self.pendingAction = None
		self.promoteQueuedDebt()
		return result

	def movePlayer(self, player, steps):
		oldPosition = player.position
		newPosition = (player.position + steps) % len(self.board)
		passedGo = False
		if (steps > 0 and newPosition < oldPosition):
			passedGo = True
		if passedGo == True:
			self.gainMoney(player.playerId, PASS_GO_YEEHAW)
		player.position = newPosition
		tile = self.board[newPosition]
		return {
			"oldPosition": oldPosition,
			"position": newPosition,
			"passedGo": passedGo,
			"tile": tile.name if tile else None
		}

	def calculateRent(self, tile, diceTotal=None):
		if tile.owner is None or tile.mortgaged:
			return 0
		if isinstance(tile, PropertyTile):
			rentIndex = min(tile.houses, len(tile.rentLevels) - 1)
			rent = tile.rentLevels[rentIndex]

			if tile.houses == 0 and self.hasColorSet(tile.owner, tile.group):
				rent *= 2
			return rent
		elif isinstance(tile, RailroadTile):
			ownerRailroads = sum(
				1 for t in self.board
				if isinstance(t, RailroadTile)
				and t.owner == tile.owner
			)
			return 25 * (2 ** (ownerRailroads - 1))
		elif isinstance(tile, UtilityTile):
			ownedUtilites = sum(
				1 for t in self.board
				if isinstance(t, UtilityTile)
				and t.owner == tile.owner
			)
			if diceTotal is None:
				return 0
			multiplier = 10 if ownedUtilites >= 2 else 4
			return diceTotal * multiplier
		return 0

	def payPendingTax(self, playerId):
		action = self.pendingAction

		if action is None or action["type"] != "debt":
			return False
		if action["playerId"] != playerId:
			return False


	def resolveTile(self, playerId, diceTotal=None):
		player = self.getPlayer(playerId)

		if player is None:
			return {"type": "error", "message": "Player not found"}
		tile = self.board[player.position]
		if tile is None:
			return {"type": "none", "message": "Empty board space"}
		if isinstance(tile, GoTile):
			return {"type": "go", "message": "Landed on GO"}
		if isinstance(tile, (PropertyTile, RailroadTile, UtilityTile)):
			if tile.owner is None:
				self.pendingAction = {
					"type": "purchase",
					"playerId": playerId,
					"position": player.position
				}
				return {
					"type": "purchase",
					"position": player.position,
					"name": tile.name,
					"price": tile.price
				}
			if tile.owner == player:
				return {
					"type": "owned",
					"name": tile.name,
					"message": "Landed on your own property"
				}
			if tile.mortgaged:
				return {
					"type": "mortgaged",
					"name": tile.name,
					"message": "No rent is due on this mortgaged property"
				}
			rent = self.calculateRent(tile, diceTotal)
			if player.money < rent:
				return self.createDebt (
					playerId,
					rent,
					"rent",
					creditorId=tile.owner.playerId,
					position=player.position
				)
			self.transferMoney(playerId, tile.owner.playerId, rent)
			return {
				"type": "rent_paid",
				"name": tile.name,
				"ownerId": tile.owner.playerId,
				"rent": rent
			}
		if isinstance(tile, TaxTile):
			if player.money < tile.amount:
				return self.createDebt (
					playerId,
					tile.amount,
					"tax"
				)
			self.painMoney(playerId, tile.amount)
			return {
				"type": "tax_paid",
				"amount": tile.amount
			}
		if isinstance(tile, GoToJailTime):
			self.sendToJail(playerId)
			return {
				"type": "sendToJail",
				"position": player.position
			}
		if isinstance(tile, JailTile):
			return {"type": "jail_visit"}
		if isinstance(tile, ChanceTile):
			drawn = card.drawCard(self.chanceDeck, self.chanceDiscard)
			return {"type": "chance", "card": drawn, "result": card.applyCardEffects(drawn, player, self, diceTotal)}
		if isinstance(tile, CommunityChestTile):
			drawn = card.drawCard(self.communityDeck, self.communityDiscard)
			return {"type": "community_chest", "card": drawn, "result": card.applyCardEffects(drawn, player, self, diceTotal)}
		if isinstance(tile, FreeParkingTile):
			return {"type": "free_parking"}
		return {"type": "none"}

	def rollNMove(self, playerId):
		if self.gameOver:
			raise GameError("The game is over.")
		if self.hasRolled == True:
			raise GameError("Already Rolled.")
		if self.pendingAction is not None:
			raise GameError("Resolve the pending action first.")
		currentPlayer = self.players[self.currentTurnIndex]
		if currentPlayer.playerId != playerId:
			raise GameError("Not your turn.")
		if currentPlayer.bankrupt:
			raise GameError("YOU'RE BANKRUPT.")

		if currentPlayer.inJail:
			dice1 = random.randint(1, 6)
			dice2 = random.randint(1, 6)
			total = dice1 + dice2
			isDouble = dice1 == dice2
			if isDouble:
				self.releaseFromJail(currentPlayer)
				move = self.movePlayer(currentPlayer, total)
				self.hasRolled = True
				effect = self.resolveTile(playerId, total)
				return {
							"dice": [dice1, dice2],
							"total": total,
							"doubles": isDouble,
							"stillInJail": False,
							**move,
							"effect": effect
						}
			else:
				currentPlayer.jailTurns += 1
				if currentPlayer.jailTurns >= MAX_JAIL_TURNS:
					# the fine goes through the debt system: paid now if affordable, otherwise the player
					# has to mortgage/sell houses or declare bankruptcy, and only leaves jail once it's paid
					# this took so long to figure out
					self.hasRolled = True
					effect = self.createDebt(playerId, JAIL_FINE, "jailFine", jailExitRoll=total)
					return 	{
								"dice": [dice1, dice2],
								"total": total,
								"doubles": isDouble,
								"stillInJail": currentPlayer.inJail,
								"effect": effect
							}
				else:
					self.hasRolled = True
					return {
						"dice": [dice1, dice2],
						"total": total,
						"doubles": False,
						"stillInJail": True
					}
		dice1 = random.randint(1, 6)
		dice2 = random.randint(1, 6)
		total = dice1 + dice2
		isDouble = dice1 == dice2

		if isDouble:
			self.doubleStreak += 1
		else:
			self.doubleStreak = 0
		if self.doubleStreak >= MAX_DOUBLES:
			self.doubleStreak = 0
			self.sendToJail(playerId)
			self.hasRolled = True
			return {
				"dice": [dice1, dice2],
				"total": total,
				"doubles": isDouble,
				"sendToJail": True
			}
		move = self.movePlayer(currentPlayer, total)
		if isDouble != True:
			self.hasRolled = True
		effect = self.resolveTile(playerId, total)
		return {
			"dice": [dice1, dice2],
			"total": total,
			"doubles": isDouble,
			**move,
			"effect": effect
		}

	def sendToJail(self, playerId):
		player = self.getPlayer(playerId)
		if player is None:
			return False
		player.position = JAIL_POSITION
		player.inJail = True
		player.jailTurns = 0
		self.doubleStreak = 0
		return True

	# shared checks for leaving jail before rolling: their turn, in jail, hasn't rolled yet
	def getJailedCurrentPlayer(self, playerId):
		if self.hasRolled:
			return None
		currentPlayer = self.players[self.currentTurnIndex]
		if currentPlayer.playerId != playerId:
			return None
		if currentPlayer.bankrupt or not currentPlayer.inJail:
			return None
		return currentPlayer

	def releaseFromJail(self, player):
		player.inJail = False
		player.jailTurns = 0

	# player still rolls normally afterwards, so hasRolled stays False
	def payJailFine(self, playerId):
		player = self.getJailedCurrentPlayer(playerId)
		if player is None:
			return False
		if player.money < JAIL_FINE:
			return False
		self.painMoney(playerId, JAIL_FINE)
		self.releaseFromJail(player)
		return True

	def useJailCard(self, playerId):
		player = self.getJailedCurrentPlayer(playerId)
		if player is None:
			return False
		if player.getOutOfJailCards <= 0:
			return False
		player.getOutOfJailCards -= 1
		self.releaseFromJail(player)
		return True

	# all() on an empty list is True, so an unknown colour must not count as owned, this function was generatedd as a test
	def hasColorSet(self, player, setColor):
		groupProperties = [
			t for t in self.board
			if isinstance(t, PropertyTile)
			and t.group == setColor
		]
		if len(groupProperties) == 0:
			return False
		return all(t.owner == player for t in groupProperties)

	def buildHouse(self, playerId, position):
		player = self.getPlayer(playerId)
		if player is None:
			return False
		if position < 0 or position >= len(self.board):
			return False
		tile = self.board[position]
		if not hasattr(tile, "owner"):
			return False
		if tile.owner != player:
			return False
		if not hasattr(tile, "houses"):
			return False
		if tile.houses >= 5:
			return False
		if tile.mortgaged:
			return False
		if player.money < tile.houseCost:
			return False
		if not self.hasColorSet(player, tile.group):
			return False

		self.painMoney(playerId, tile.houseCost)
		tile.houses += 1
		return True

	def endTurn(self, playerId):
		if self.gameOver:
			return False
		if self.hasRolled != True:
			return False
		# a purchase, auction or debt must be settled before the turn can pass
		if self.pendingAction is not None:
			raise GameError("Resolve the pending action first.")
		currentPlayer = self.players[self.currentTurnIndex]
		if currentPlayer.playerId != playerId:
			return False
		self.currentTurnIndex += 1
		if self.currentTurnIndex >= len(self.players):
			self.currentTurnIndex = 0
		while self.players[self.currentTurnIndex].bankrupt:
			self.currentTurnIndex += 1
			if self.currentTurnIndex >= len(self.players):
				self.currentTurnIndex = 0
		self.hasRolled = False
		return True

	def gainMoney(self, ID, amount):
		player = self.getPlayer(ID)
		if player is None:
			return False
		player.money += amount
		return True

	#(as in the pain of losing money)
	def painMoney(self, ID, amount):
		player = self.getPlayer(ID)
		if player is None:
			return False
		player.money -= amount
		return True

	def transferMoney(self, fromID, toID, amount):
		fromPlayer = self.getPlayer(fromID)
		toPlayer = self.getPlayer(toID)

		if fromPlayer is None or toPlayer is None:
			return False
		fromPlayer.money -= amount
		toPlayer.money += amount
		return True

	def	getPlayer(self, ID):
		for p in self.players:
			if p.playerId == ID:
				return p
		print ("[DEBUG] Player Not Found")
		return None

	# =============================================
	# DEBT
	# =============================================

	# jailExitRoll: dice total to move by once a jail fine is paid, None for every other debt
	def createDebt(self, playerId, amount, reason, creditorId=None, position=None, jailExitRoll=None):
		player = self.getPlayer(playerId)

		if player is None or player.bankrupt:
			return False
		if amount < 0:
			return False
		debt = {
			"type": "debt",
			"playerId": playerId,
			"creditorId": creditorId,
			"amount": amount,
			"reason": reason,
			"position": position,
			"jailExitRoll": jailExitRoll
		}
		# something else is already pending, so this debt waits its turn
		if self.pendingAction is not None:
			self.debtQueue.append(debt)
			return {
				"type": "debt_queued",
				"playerId": playerId,
				"amount": amount,
				"reason": reason
			}
		self.pendingAction = debt
		return self.resolveDebt(playerId)

	# move the next queued debt into pendingAction once it's free, paying it straight away if affordable
	def promoteQueuedDebt(self):
		while self.pendingAction is None and self.debtQueue and not self.gameOver:
			debt = self.debtQueue.pop(0)
			player = self.getPlayer(debt["playerId"])
			if player is None or player.bankrupt:
				continue
			self.pendingAction = debt
			self.resolveDebt(debt["playerId"])

	def resolveDebt(self, playerId):
		debt = self.pendingAction

		if debt is None or debt["type"] != "debt":
			return False
		if debt["playerId"] != playerId:
			return False
		player = self.getPlayer(playerId)
		if player is None or player.bankrupt:
			return False
		if player.money < debt["amount"]:
			return {
				"type": "debt",
				"amount": debt["amount"],
				"shortfall": debt["amount"] - player.money,
				"reason": debt["reason"],
				"canPay": False
			}
		amount = debt["amount"]
		creditorId = debt["creditorId"]

		if creditorId is None:
			self.painMoney(playerId, amount)
		else:
			if not self.transferMoney(playerId, creditorId, amount):
				return False
		self.pendingAction = None
		result = {
			"type": "debt_paid",
			"amount": amount,
			"reason": debt["reason"]
		}
		# jail fine paid, so the player can now leave jail and move by the roll that was on hold
		jailExitRoll = debt.get("jailExitRoll")
		if jailExitRoll is not None:
			self.releaseFromJail(player)
			move = self.movePlayer(player, jailExitRoll)
			result["jailExit"] = {**move, "effect": self.resolveTile(playerId, jailExitRoll)}
		self.promoteQueuedDebt()
		return result

	def sellHouse(self, playerId, position):
		player = self.getPlayer(playerId)

		if player is None or player.bankrupt:
			return False
		if position < 0 or position >= len(self.board):
			return False
		tile = self.board[position]

		if not isinstance(tile, PropertyTile):
			return False
		if tile.owner != player:
			return False
		if tile.houses <= 0:
			return False
		groupProperties = [
			t for t in self.board
			if isinstance(t, PropertyTile)
			and t.group == tile.group
			and t.owner == player
		]
		if groupProperties:
			maximumHouses = max(t.houses for t in groupProperties)
			if tile.houses < maximumHouses:
				return False
		tile.houses -= 1
		refund = tile.houseCost // 2
		player.money += refund
		result = {
			"success": True,
			"refund": refund,
			"housesRemaining": tile.houses,
		}
		if self.pendingAction is not None and self.pendingAction["type"] == "debt":
			if self.pendingAction["playerId"] == playerId:
				result["debt"] = self.resolveDebt(playerId)
		return result

	# ============================================

	def declareBankruptcy(self, playerId):
		player = self.getPlayer(playerId)
		if not player:
			return False
		debt = self.pendingAction

		if not debt or debt["type"] != "debt":
			return False
		if debt["playerId"] != playerId:
			return False
		if player.money >= debt["amount"]:
			return False
		for position in player.properties:
			tile = self.board[position]
			if isinstance(tile, PropertyTile) and tile.houses > 0:
				return False
		for position in player.properties:
			tile = self.board[position]
			if hasattr(tile, "mortgaged") and not tile.mortgaged:
				return False
		player = self.getPlayer(playerId)

		if player is None or player.bankrupt:
			return False
		if player.money >= debt["amount"]:
			return False
		creditorId = debt["creditorId"]
		creditor = self.getPlayer(creditorId) if creditorId is not None else None

		if creditorId is not None and creditor is None:
			return False
		for position in list(player.properties):
			tile = self.board[position]

			if creditor is not None:
				tile.owner = creditor
				creditor.properties.append(position)
			else:
				tile.owner = None
				tile.mortgaged = False
			player.properties.remove(position)
		player.bankrupt = True
		if creditor is not None:
			creditor.money += player.money
		player.money = 0
		player.inJail = False
		player.jailTurns = 0
		player.getOutOfJailCards = 0
		self.pendingAction = None
		winner = self.checkGameOver()
		self.promoteQueuedDebt()

		return {
			"type": "bankruptcy",
			"playerId": playerId,
			"creditorId": creditorId,
			"winner": winner
		}

	def checkGameOver(self):
		remainingPlayers = [
			p for p in self.players
			if not p.bankrupt
		]
		if len(remainingPlayers) <= 1:
			self.gameOver = True
			self.winnerId = (
				remainingPlayers[0].playerId
				if remainingPlayers else None
			)
			return self.winnerId
		return None

	def validateTradeProperties(self, player, positions):
		if not isinstance(positions, list):
			return False
		if len(positions) != len(set(positions)):
			return False
		for position in positions:
			if not isinstance(position, int) or isinstance(position, bool):
				return False
			if position < 0 or position >= len(self.board):
				return False
			tile = self.board[position]
			if not isinstance(tile, (PropertyTile, RailroadTile, UtilityTile)):
				return False
			if tile.owner != player:
				return False
			if isinstance(tile, PropertyTile):
				for groupTile in self.board:
					if isinstance(groupTile, PropertyTile) and groupTile.group == tile.group and groupTile.houses > 0:
						return False
		return True

	def proposeTrade(self, fromPlayerId, toPlayerId, offerProperties=None, requestProperties=None, offerMoney=0, requestMoney=0, offerJailCards=0, requestJailCards=0):
		fromPlayer = self.getPlayer(fromPlayerId)
		toPlayer = self.getPlayer(toPlayerId)

		if fromPlayer is None or toPlayer is None:
			return False
		if fromPlayer == toPlayer:
			return False
		if fromPlayer.bankrupt or toPlayer.bankrupt:
			return False
		offerProperties = offerProperties or []
		requestProperties = requestProperties or []
		amounts = [offerMoney, requestMoney, offerJailCards, requestJailCards]

		for amount in amounts:
			if not isinstance(amount, int) or isinstance(amount, bool):
				return False
			if amount < 0:
				return False



	def acceptTrade(self, playerId, tradeId):
		trade = self.tradeOffers.get(tradeId)

		if trade is None:
			return False
		if trade["toPlayerId"] != playerId:
			return False
		fromPlayer = self.getPlayer(trade["fromPlayerId"])
		toPlayer = self.getPlayer(trade["toPlayerId"])

		if fromPlayer is None or toPlayer is None:
			return False
		if fromPlayer.bankrupt or toPlayer.bankrupt:
			return False
		offerProperties = trade["offerProperties"]
		requestProperties = trade["requestProperties"]

		if not self.validateTradeProperties(fromPlayer, offerProperties):
			return False
		if not self.validateTradeProperties(toPlayer, requestProperties):
			return False
		offerMoney = trade["offerMoney"]
		requestMoney = trade["requestMoney"]
		offerCards = trade["offerJailCards"]
		requestCards = trade["requestJailCards"]

		if fromPlayer.money < offerMoney:
			return False
		if toPlayer.money < requestMoney:
			return False
		if fromPlayer.getOutOfJailCards < offerCards:
			return False
		if toPlayer.getOutOfJailCards < requestCards:
			return False
		fromInterest = sum(
			int(self.board[position].mortgageValue * 0.10)
			for position in requestProperties
			if self.board[position].mortgaged
		)
		toInterest = sum(
			int(self.board[position].mortgageValue * 0.10)
			for position in offerProperties
			if self.board[position].mortgaged
		)
		fromBalace = fromPlayer.money - offerMoney + requestMoney - fromInterest
		toBalance = toPlayer.money - requestMoney + offerMoney - toInterest

		if fromBalace < 0 or toBalance < 0:
			return False
		fromPlayer.money = fromBalace
		toPlayer.money = toBalance
		for position in offerProperties:
			fromPlayer.properties.remove(position)
			toPlayer.properties.append(position)
			self.board[position].owner = toPlayer
		for position in requestProperties:
			toPlayer.properties.remove(position)
			fromPlayer.properties.append(position)
			self.board[position].owner = fromPlayer
		fromPlayer.getOutOfJailCards -= offerCards
		fromPlayer.getOutOfJailCards += requestCards
		toPlayer.getOutOfJailCards -= requestCards
		toPlayer.getOutOfJailCards += offerCards

		del self.tradeOffers[tradeId]
		return {
			"type": "trade_accepted",
			"tradeId": tradeId,
			"fromPlayerId": fromPlayer.playerId,
			"toPlayerId": toPlayer.playerId
		}

	def rejectTrade(self, playerId, tradeId):
		trade = self.tradeOffers.get(tradeId)

		if trade is None:
			return False
		if trade["toPlayerId"] != playerId:
			return False
		del self.tradeOffers[tradeId]
		return {
			"type": "trade_rejected",
			"tradeId": tradeId
		}

	def getState(self, playerId):
		player = self.getPlayer(playerId)

		if player is None:
			return None
		return {
			"currentTurn": self.players[self.currentTurnIndex].playerId,
			"hasRolled": self.hasRolled,
			"doubleStreak": self.doubleStreak,
			"gameOver": self.gameOver,
			"winnerId": self.winnerId,
			"pendingAction": self.pendingAction,
			"auction": self.auctionState,
			"debtQueue": self.debtQueue,
			"tradeOffers": list(self.tradeOffers.values()),
			"player": {
				"id": player.playerId,
				"name": player.name,
				"position": player.position,
				"money": player.money,
				"properties": player.properties,
				"inJail": player.inJail,
				"jailTurns": player.jailTurns,
				"getOutOfJailCards": player.getOutOfJailCards,
				"bankrupt": player.bankrupt,
			},
			"players": [
				{
					"id": p.playerId,
					"name": p.name,
					"position": p.position,
					"money": p.money,
					"bankrupt": p.bankrupt,
					"properties": p.properties,
					"inJail": p.inJail,
					"getOutOfJailCards": p.getOutOfJailCards
				}
					for p in self.players
			],
			"board": [
				{
					"position": tile.position,
					"name": tile.name,
					"type": type(tile).__name__,
					"group": getattr(tile, "group", None),
					"price": getattr(tile, "price", None),
					"owner": tile.owner.playerId if getattr(tile, "owner", None) else None,
					"houses": getattr(tile, "houses", 0),
					"mortgaged": getattr(tile, "mortgaged", False)
				}
				if tile else None
				for tile in self.board
			]
		}
#we use getattr because we might want the actual value not just booleans, nobody should know the state of the decks except ME (cheat modes)

class GameServer:
	def __init__(self):
		self.games = {}

	def getState(self, gameId, playerId):
		game = self.getGame(gameId)

		if game is None:
			return {
				"success": False,
				"error": "Game not found"
			}

		state = game.getState(playerId)
		if state is None:
			return {
				"success": False,
				"error": "Player not found"
			}
		return {
			"success": True,
			"state": state
		}

	def createGame(self, gameId, players, board):
		if gameId in self.games:
			return False
		self.games[gameId] = Game(board, players)
		return True

	def getGame(self, gameId):
		return self.games.get(gameId)

	def act(self, gameId, playerId, action, **params):
		game = self.getGame(gameId)
		if game is None:
			return {"success": False, "error": "Game not found"}
		methodName = ACTIONS.get(action)
		if methodName is None:
			return {"success": False, "error": f"Unknown action '{action}'"}
		# optional request fields arrive as None, don't pass them to methods that don't take them
		params = {key: value for key, value in params.items() if value is not None}
		try:
			result = getattr(game, methodName)(playerId, **params)
			if result is False:
				return {"success": False, "error": f"Cannot {action} right now"}
			return {"success": True, "result": result, "state": game.getState(playerId)}
		except GameError as e:
			return {"success": False, "error": str(e)}
