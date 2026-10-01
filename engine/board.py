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

	board = [None] * data["board_size"]
	for tileData in data["tiles"]:
		tileType = tileData.pop("type")
		position = tileData["position"]
		cls = TILE_CLASSES[tileType]
		board[position] = cls(**tileData)
	return board