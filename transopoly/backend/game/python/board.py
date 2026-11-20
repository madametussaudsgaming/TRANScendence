# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    board.py                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: rpadasia <ryanpadasian@gmail.com>          +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/14 13:56:40 by alechin           #+#    #+#              #
#    Updated: 2026/11/08 14:20:59 by rpadasia         ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import json

from tile import Tile
from tile import PropertyTile
from tile import RailroadTile
from tile import UtilityTile
from tile import TaxTile
from tile import ChanceTile
from tile import CommunityChestTile
from tile import GoTile
from tile import JailTile
from tile import FreeParkingTile
from tile import GoToJailTime

# ------------------------
# BOARD LOGIC
# ------------------------

TILE_CLASSES = {
	"go": GoTile,
	"property": PropertyTile,
	"railroad": RailroadTile,
	"utility": UtilityTile,
	"tax": TaxTile,
	"chance": ChanceTile,
	"communityChest": CommunityChestTile,
	"jail": JailTile,
	"freeParking": FreeParkingTile,
	"goToJail": GoToJailTime,
}

def loadBoard(path):
	with open(path) as f:
		data = json.load(f)

	boardSize = data["board_size"]
	board = [None] * boardSize
	for tileData in data["tiles"]:
		tileType = tileData["type"]
		position = tileData["position"]

		if tileType not in TILE_CLASSES:
			raise ValueError(f"Unknown tile type: {tileType}")
		if position < 0 or position >= boardSize:
			raise ValueError(f"Invalid tile position: {tileType}")
		if board[position] is not None:
			raise ValueError(f"Duplicate tile position: {position}")
		cls = TILE_CLASSES[tileType]
		tileArgs = {
			key: value
			for key, value in tileData.items()
			if key != "type"
		}
		board[position] = cls(**tileArgs)
	if any(tile is None for tile in board):
		missing = [
			i for i, tile in enumerate(board)
			if tile is None
		]
		raise ValueError(f"Missing board position: {missing}")
	return board