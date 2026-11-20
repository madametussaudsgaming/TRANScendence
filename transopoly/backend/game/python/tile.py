# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    tile.py                                            :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: alechin <alechin@student.42kl.edu.my>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/14 12:53:47 by alechin           #+#    #+#              #
#    Updated: 2026/09/14 12:53:47 by alechin          ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

# -------------------------------------------------------------
# TILES
# -------------------------------------------------------------

class Tile:
	def __init__(self, name, position):
		self.name = name
		self.position = position

class PropertyTile(Tile):
	def __init__(self, name, position, price, group, rentLevels, houseCost, mortgageValue):
		super().__init__(name, position)
		self.price = price
		self.group = group
		self.rentLevels = rentLevels
		self.houseCost = houseCost
		self.mortgageValue = mortgageValue
		self.owner = None
		self.houses = 0
		self.mortgaged = False

class RailroadTile(Tile):
	def __init__(self, name, position, price, mortgageValue):
		super().__init__(name, position)
		self.price = price
		self.mortgageValue = mortgageValue
		self.owner = None
		self.mortgaged = False

class UtilityTile(Tile):
	def __init__(self, name, position, price, mortgageValue):
		super().__init__(name, position)
		self.price = price
		self.mortgageValue = mortgageValue
		self.owner = None
		self.mortgaged = False


class TaxTile(Tile):
	def __init__(self, name, position, amount):
		super().__init__(name, position)
		self.amount = amount

class ChanceTile(Tile):
	def __init__(self, name, position):
		super().__init__(name, position)
	pass

class CommunityChestTile(Tile):
	def __init__(self, name, position):
		super().__init__(name, position)
	pass

class GoTile(Tile):
	def __init__(self, name, position):
		super().__init__(name, position)
	pass

class JailTile(Tile):
	def __init__(self, name, position):
		super().__init__(name, position)
	pass

class FreeParkingTile(Tile):
	def __init__(self, name, position):
		super().__init__(name, position)
	pass

class GoToJailTime(Tile):
	def __init__(self, name, position):
		super().__init__(name, position)
	pass