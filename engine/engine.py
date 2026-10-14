# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    engine.py                                          :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: rpadasia <ryanpadasian@gmail.com>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/14 14:28:44 by alechin           #+#    #+#              #
#    Updated: 2026/10/13 22:31:12 by rpadasia         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import random
JAIL_POSITION = 10
JAIL_FINE = 50
MAX_JAIL_TURNS = 3


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
		if len(self.players) < 2 or len(self.players > 4):
			return False
		if len(self.players) >= 2:
			return True
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
		self.hasRolled = 0

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

	def rollNMove(self, playerId):
		player = self.getPlayer(playerId)
		if player is None:
			return False
		if self.hasRolled == True:
			return False
		currentPlayer = self.players[self.currentTurnIndex]
		if currentPlayer.playerId != playerId:
			return False
		if player.bankrupt:
			return False
		if player.inJail:
			prompt = 0

			#prompt the current player if they want to pay the fine or roll doubles
			if (prompt == 'pay'):
				self.painMoney(playerId, JAIL_FINE)
			else:
				dice1 = random.randint(1, 6)
				dice2 = random.randint(1, 6)
				total = dice1 + dice2
				isDouble = dice1 == dice2
				if isDouble:
					player.jailTurns = 0
					player.inJail = False
				else:
					if player.jailTurns > 2:
						self.painMoney(playerId, JAIL_FINE)
						player.inJail = False
						player.jailTurns = 0
					player.jailTurns += 1
					player.inJail = True
					return {
								"dice": [dice1, dice2],
								"total": total,
								"doubles": isDouble,
								"oldPosition": oldPosition,
								"position": player.position,
								"tile": tile.name if tile else None
							}

		dice1 = random.randint(1, 6)
		dice2 = random.randint(1, 6)
		total = dice1 + dice2
		isDouble = dice1 == dice2

		if isDouble:
			self.doubleStreak += 1
		else:
			self.doubleStreak = 0
		if self.doubleStreak >= MAX_JAIL_TURNS:
			self.doubleStreak = 0
			self.sendToJail(playerId)
			return {
				"dice": [dice1, dice2],
				"total": total,
				"doubles": isDouble,
				"sendToJail": True
			}
		oldPosition = player.position
		player.position += total

		if player.position >= len(self.board):
			player.position -= len(self.board)
			player.money += 200
		tile = self.board[player.position]
		if isDouble != True:
			self.hasRolled = False
		return {
			"dice": [dice1, dice2],
			"total": total,
			"doubles": isDouble,
			"oldPosition": oldPosition,
			"position": player.position,
			"tile": tile.name if tile else None
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
		player = self.getPlayer(playerId)
		if player is None:
			return False
		currentPlayer = self.players[self.currentTurnIndex]
		if currentPlayer.playerId != playerId:
			return False
		if self.doubleStreak > 0:
			self.doubleStreak = 0
			return True
		self.currentTurnIndex += 1
		if self.currentTurnIndex >= len(self.players):
			self.currentTurnIndex = 0
		while self.players[self.currentTurnIndex].bankrupt:
			self.currentTurnIndex += 1
			if self.currentTurnIndex >= len(self.players):
				self.currentTurnIndex = 0
		self.hasRolled = 0
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
					"mortgaged": tile.mortgaged if hasattr(tile, "mortgage") else False
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