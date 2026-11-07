# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    engine.py                                          :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: rpadasia <ryanpadasian@gmail.com>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/14 14:28:44 by alechin           #+#    #+#              #
#    Updated: 2026/10/14 16:31:50 by rpadasia         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import random

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

JAIL_POSITION = 10
JAIL_FINE = 50
MAX_JAIL_TURNS = 3
MAX_DOUBLES = 3
PASS_GO_YEEHAW = 200

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

	def buyProperty(self, playerId, position):
		player = self.getPlayer(playerId)
		if player is None:
			return False
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
		if self.pendingAction is not None:
			if self.pendingAction["playerId"] == playerId:
				self.resolveDebt(playerId)
		return True

	def auction(self, position):
		action = self.pendingAction
		
		if action is not None:
			if action["type"] != "purchase":
				return False
			if action["purchase"] != position:
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
			if winner.money < winningBid or tile.owner is not None:
				return False
			winner.money -= 1
			winner.properties.append(position)
			tile.owner = winner
			result = {
				"type": "auction_ended",
				"winnerId": winnerId,
				"winningBid": winningBid,
				"position": position,
				"name": tile.name
			}
		self.auctionState = None
		self.pendingAction = None
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
			if tile.houses == 0:
				groupProperties = [
					t for t in self.board
					if isinstance(t, PropertyTile)
					and t.group == tile.group
				]
				if groupProperties and all(t.owner == tile.owner for t in groupProperties):
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
			return {"type": "chance"}
		if isinstance(tile, CommunityChestTile):
			return {"type": "community_chance"}
		if isinstance(tile, FreeParkingTile):
			return {"type": "free_parking"}
		return {"type": "none"}

	def rollNMove(self, playerId):
		if self.gameOver:
			return False
		if self.hasRolled == True:
			return False
		if self.pendingAction is not None:
			return False
		currentPlayer = self.players[self.currentTurnIndex]
		if currentPlayer.playerId != playerId:
			return False
		if currentPlayer.bankrupt:
			return False

		if currentPlayer.inJail:
			dice1 = random.randint(1, 6)
			dice2 = random.randint(1, 6)
			total = dice1 + dice2
			isDouble = dice1 == dice2
			if isDouble:
				self.releaseFromJail(currentPlayer)
				move = self.movePlayer(currentPlayer, total)
				self.hasRolled = True
				return {
							"dice": [dice1, dice2],
							"total": total,
							"doubles": isDouble,
							"stillInJail": False,
							**move
						}
			else:
				currentPlayer.jailTurns += 1
				if currentPlayer.jailTurns >= MAX_JAIL_TURNS:
					self.painMoney(playerId, JAIL_FINE)
					# TODO: bankruptcy if money < 0.
					self.releaseFromJail(currentPlayer)
					self.hasRolled = True
					move = self.movePlayer(currentPlayer, total)
					return 	{
								"dice": [dice1, dice2],
								"total": total,
								"doubles": isDouble,
								"stillInJail": False,
								**move
							}
				else:
					currentPlayer.jailTurns += 1
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
		return {
			"dice": [dice1, dice2],
			"total": total,
			"doubles": isDouble,
			**move
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

		# TODO -> check whether the player has ALL its respective colored groups

		player.money -= tile.houseCost
		tile.houses += 1
		return True

	def endTurn(self, playerId):
		if self.gameOver:
			return False
		if self.hasRolled != True:
			return False
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

	def createDebt(self, playerId, amount, reason, creditorId=None, position=None):
		player = self.getPlayer(playerId)

		if player is None or player.bankrupt:
			return False
		if self.pendingAction is not None:
			return False
		if amount < 0:
			return False
		self.pendingAction = {
			"type": "debt",
			"playerId": playerId,
			"creditorId": creditorId,
			"amount": amount,
			"reason": reason,
			"position": position
		}
		return self.resolveDebt(playerId)

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
		return {
			"type": "debt_paid",
			"amount": amount,
			"reason": debt["reason"]
		}

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
			minimumHouses = min(t.houses for t in groupProperties)
			if tile.houses <= minimumHouses:
				return False
		tile.houses -= 1
		refund = tile.houseCost // 2
		player.money += refund
		result = {
			"success": True,
			"refund": refund,
			"housesRemaining": tile.houses,
		}
		if self.pendingAction is not None:
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

	def validateTradeProperties(self, player, position):
		if not isinstance(position, list):
			return False
		if len(position) != len(set(position)):
			return False
		for position in positions:
			if not isinstance(position, int) or isinstance(position, bool):
				return False
			if position < 0 or position >= len(self.board):
				return False
			tile = self.board[position]
			if not isinstance(tile, (PropertyTile, RailroadTile, UtilityTile)):
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
		from position in offerProperties:
			fromPlayer.properties.remove(position)
			toPlayer.properties.append(position)
			self.board[position].owner = toPlayer
		from position in requestProperties:
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
				"gameOver": self.gameOver,
				"winnerId": self.winnerId
			},
			"players": [
				{
					"id": p.playerId,
					"name": p.name,
					"position": p.position,
					"money": p.money,
					"bankrupt": p.bankrupt
				}
					for p in self.players
			],
			"board": [
				{
					"position": tile.position,
					"name": tile.name,
					"owner": tile.owner.playerId if hasattr(tile, "owner") and tile.owner else None,
					"houses": tile.houses if hasattr(tile, "houses") else 0,
					"mortgaged": tile.mortgaged if hasattr(tile, "mortgaged") else False
				}
				if tile else None
				for tile in self.board
			]
		}

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

	def roll(self, gameId, playerId):
		game = self.games.get(gameId)

		if game is None:
			return {
				"success": False,
				"error": "There is no game."
			}
		result = game.rollNMove(playerId)
		if result is False:
			return {
				"success": False,
				"error": "Unable to roll"
			}
		return {
			"success": True,
			"result": result,
			"state": game.getState(playerId)
		}

	def payJailFine(self, gameId, playerId):
		game = self.games.get(gameId)

		if game is None:
			return {
				"success": False,
				"error": "There is no game."
			}
		if not game.payJailFine(playerId):
			return {
				"success": False,
				"error": "Unable to pay jail fine"
			}
		return {
			"success": True,
			"state": game.getState(playerId)
		}

	def useJailCard(self, gameId, playerId):
		game = self.games.get(gameId)

		if game is None:
			return {
				"success": False,
				"error": "There is no game."
			}
		if not game.useJailCard(playerId):
			return {
				"success": False,
				"error": "Unable to use get out of jail card"
			}
		return {
			"success": True,
			"state": game.getState(playerId)
		}

	def declinePurchase(self, gameId, playerId):
		game = self.getGame(gameId)

		if game is None:
			return {
				"success": False,
				"error": "There is no game"
			}
		result = game.declinePurchase(playerId)
		if result is False:
			return {
				"success": False,
				"error": "Unable to decline purchase"
			}
		return {
			"success": True,
			"result": result,
			"state": game.getState(playerId)
		}

	def placeBid(self, gameId, playerId, amount):
		game = self.getGame(gameId)

		if game is None:
			return {
				"success": False,
				"error": "There is no game"
			}
		result = game.placeBid(playerId, amount)
		if result is False:
			return {
				"success": False,
				"error": "Unable to place bid"
			}
		return {
			"success": True,
			"result": result,
			"state": game.getState(playerId)
		}

	def passAuction(self, gameId, playerId):
		game = self.getGame(gameId)

		if game is None:
			return {
				"success": False,
				"error": "There is no game"
			}
		result = game.passAuction(playerId)
		if result is False:
			return {
				"success": False,
				"error": "Unable to pass auction"
			}
		return {
			"success": True,
			"result": result,
			"state": game.getState(playerId)
		}