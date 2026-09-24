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
		pass

	def mortgage(self, playerId, position):
		pass

	def auction(self):
		pass

	def rollNMove(self, playerId):
		pass

	def sendToJail(self):
		pass

	def buildHouse(self, playerId, position):
		pass

	def endTurn(self, playerId):
		pass

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
