# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    board.py                                           :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: alechin <alechin@student.42kl.edu.my>      +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/09/14 13:56:40 by alechin           #+#    #+#              #
#    Updated: 2026/09/14 13:56:40 by alechin          ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import json

from prototype.tile import Tile
from prototype.tile import PropertyTile
from prototype.tile import RailroadTile
from prototype.tile import UtilityTile
from prototype.tile import TaxTile
from prototype.tile import ChanceTile
from prototype.tile import CommunityChestTile
from prototype.tile import GoTile
from prototype.tile import JailTile
from prototype.tile import FreeParkingTile
from prototype.tile import GoToJailTime

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

	board = [None] * data["boardSize"]
	for tileData in data["tiles"]:
		tileType = tileData.pop("type")
		position = tileData["position"]
		cls = TILE_CLASSES[tileType]
		board[position] = cls(**tileData)
	return board