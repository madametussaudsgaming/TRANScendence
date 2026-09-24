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


class preGame:
	# while in lobby
	# when receive enter button, take user credentials and username (protect from sql injection), make a temp player, add to an array
	# when every player currently joined presses 'ready' OR 4 players have been reached, then a countdown of 10 seconds happens then the game starts.
	#if a player disconnects during this time, then everyone's no longer ready. if somebody clicks the button again (un-ready) everyone is no longer ready


	def __init__(self):
		self.players = []

	def	getTempPlayer(self, ID):
		for p in self.players:
			if p.playerID == ID:
				return p
		print ("[DEBUG] Player Not Found")

	def tempPlayerJoin(self, ID, username):
		self.players.append(Player(ID, username))

	def tempPlayerLeft(self, ID):
		target = self.getTempPlayer(ID)
		self.players.remove(target)

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

	def buyProperty(playerId, position):
		pass

	def mortgage(playerId, position):
		pass

	def auction():
		pass

	def rollNMove(playerId):
		pass

	def sendToJail():
		pass

	def buildHouse(playerId, position):
		pass

	def endTurn(playerId):
		pass

	def	getPlayer(self, ID):
			for p in self.players:
				if p.playerID == ID:
					return p
			print ("[DEBUG] Player Not Found")

	def getState(self, playerId):
		player = self.players[playerId]
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
				"getOutOfJailCaards": player.getOutOfJailCards,
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
