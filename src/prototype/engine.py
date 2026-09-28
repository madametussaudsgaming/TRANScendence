# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    player.py                                          :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: alechin <alechin@student.42kl.edu.my>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/14 14:28:44 by alechin           #+#    #+#              #
#    Updated: 2026/09/14 14:28:44 by alechin          ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import random

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
			if p.playerID == ID:
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
		if len(self.players) >= 4:
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
		currentPlayer = self.players[self.currentTurnIndex]
		if currentPlayer.playerId != playerId:
			return False
		if player.bankrupt:
			return False
		if player.inJail:
			return False

		dice1 = random.randint(1, 6)
		dice2 = random.randint(1, 6)
		total = dice1 + dice2
		isDouble = dice1 == dice2

		if isDouble:
			self.doubleStreak += 1
		else:
			self.doubleStreak = 0
		if self.doubleStreak >= 3:
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
		player.position = 10
		player.inJail = True
		player.jailTurns = 0
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
		currentPlayer = self.players
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
		return True

	def gainMoney(self, ID, amount):
		player = Game.getPlayer(ID)
		if player is None:
			return False
		player.money += amount
		return True
	
	#(as in the pain of losing money)
	def painMoney(self, ID, amount):
		player = Game.getPlayer(ID)
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
			if p.playerID == ID:
				return p
		print ("[DEBUG] Player Not Found")
		return None

	def getState(self, playerId):
		player = self.getPlayer(playerId)
		return {
			"currentTurn": self.currentTurnIndex,
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
					"mortgage": tile.mortgaged if hasattr(tile, "mortgage") else False
				}
				if tile else None
				for tile in self.board
			]
		}

class GameServer:
	def __init__(self):
		self.games = {}

	def createGame():
		pass

	def getGame():
		pass

	def roll():
		pass