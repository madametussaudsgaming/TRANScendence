# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    engine.py                                          :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: rpadasia <ryanpadasian@gmail.com>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/14 14:28:44 by alechin           #+#    #+#              #
#    Updated: 2026/10/31 16:27:14 by rpadasia         ###   ########.fr        #
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

ACTIONS = {
	"roll":     "rollNMove",
	"buy":      "buyProperty",
	"decline":  "declinePurchase",
	"endTurn":  "endTurn",
	"mortgage": "mortgage",
	"build":    "buildHouse",
	"jailPay":  "payJailFine",
	"jailCard": "useJailCard",
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
		playerCount = len(self.players)

		if playerCount < 2 or playerCount > 4:
			return False
		return self.allPlayerReady()

	def startGame(self):
		if not self.canStart():
			return None
		self.started = True
		return self.players

	#ONCE REACCHED WE"RE USING WEBSOCKETS, leaveGame and startGame on the website side
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
		return True

	# need to begin an auction after this
	def declinePurchase(self, playerId):
		action = self.pendingAction
		if action is None:
			return False
		if action["type"] != "purchase":
			return False
		if action["playerId"] != playerId:
			return False
		self.pendingAction = None
		return True

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
		return True

	def auction(self, position):
		if position < 0 or position >= len(self.board):
			return False
		tile = self.board[position]
		if not hasattr(tile, "price"):
			return False
		if tile.owner is not None:
			return False

		# TODO -> Build the actual bidding when the website is actually up

		return True

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

	# basically what happens to the gamestate when a player goes to a new tile
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
				return {
					"type": "rent_due",
					"name": tile.name,
					"ownerId": tile.owner.playerId,
					"rent": rent,
					"canPay": False
				}
			self.transferMoney(playerId, tile.owner.playerId, rent)
			return {
				"type": "rent_paid",
				"name": tile.name,
				"ownerId": tile.owner.playerId,
				"rent": rent
			}
		if isinstance(tile, TaxTile):
			if player.money < tile.amount:
				return {
					"type": "tax_due",
					"amount": tile.amount,
					"canPay": False,
				}
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
		if self.hasRolled == True:
			raise GameError("Already Rolled.")
		if self.pendingAction is not None:
			raise GameError("Decide on the pending purchase first.")
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
					# normal roll
					self.hasRolled = True
					move = self.movePlayer(currentPlayer, total)
					if not isDouble:
						self.hasRolled = True
					effect = self.resolveTile(playerId, total)
					return 	{
								"dice": [dice1, dice2],
								"total": total,
								"doubles": isDouble,
								**move,
								"effect": effect
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

	def getState(self, playerId):
		player = self.getPlayer(playerId)
		if player is None: return None
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
				"bankrupt": player.bankrupt
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

	def act(self, gameId, playerId, action, **params):
		game = self.getGame(gameId)
		if game is None:
			return {"success": False, "error": "Game not found"}
		methodName = ACTIONS.get(action)
		if methodName is None:
			return {"success": False, "error": f"Unknown action '{action}'"}
		try:
			result = getattr(game, methodName)(playerId, **params)
			if result is False:
				return {"success": False, "error": f"Cannot {action} right now"}
			return {"success": True, "result": result, "state": game.getState(playerId)}
		except GameError as e:
			return {"success": False, "error": str(e)}

	# def roll(self, gameId, playerId):
	# 	game = self.games.get(gameId)

	# 	if game is None:
	# 		return {
	# 			"success": False,
	# 			"error": "There is no game."
	# 		}
	# 	result = game.rollNMove(playerId)
	# 	if result is False:
	# 		return {
	# 			"success": False,
	# 			"error": "Unable to roll"
	# 		}
	# 	return {
	# 		"success": True,
	# 		"result": result,
	# 		"state": game.getState(playerId)
	# 	}

	# def payJailFine(self, gameId, playerId):
	# 	game = self.games.get(gameId)

	# 	if game is None:
	# 		return {
	# 			"success": False,
	# 			"error": "There is no game."
	# 		}
	# 	if not game.payJailFine(playerId):
	# 		return {
	# 			"success": False,
	# 			"error": "Unable to pay jail fine"
	# 		}
	# 	return {
	# 		"success": True,
	# 		"state": game.getState(playerId)
	# 	}

	# def useJailCard(self, gameId, playerId):
	# 	game = self.games.get(gameId)

	# 	if game is None:
	# 		return {
	# 			"success": False,
	# 			"error": "There is no game."
	# 		}
	# 	if not game.useJailCard(playerId):
	# 		return {
	# 			"success": False,
	# 			"error": "Unable to use get out of jail card"
	# 		}
	# 	return {
	# 		"success": True,
	# 		"state": game.getState(playerId)
	# 	}