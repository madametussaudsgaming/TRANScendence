from fastapi import FastAPI
from pydantic import BaseModel
from board import loadBoard
from engine import GameServer, Player
from typing import Literal, Optional


app = FastAPI()
server = GameServer()

class PlayerData(BaseModel):
	playerId: int
	name: str

class CreateGameRequest(BaseModel):
	gameId: str
	players: list[PlayerData]

# class RollRequest(BaseModel):
# 	playerId: int

class ActionRequest(BaseModel):
	playerId: int
	action: Literal[
		"roll",
		"buy",
		"decline",
		"endTurn",
		"mortgage",
		"build",
		"jailPay",
		"jailCard",
		"bid",
		"passAuction"
	]
	position: Optional[int] = None
	amount: Optional[int] = None

def act(self, gameId, playerId, action, **params):
	game = self.getGame(gameId)

	if game is None:
		return {"success": False, "error": "There is no game"}
	result = False

	if action == "roll":
		return self.roll(gameId, playerId)
	elif action == "buy":
		result = game.buyProperty(playerId, params.get("position", -1))
	elif action == "decline":
		result = game.declinePurchase(playerId)
	elif action == "bid":
		amount = params.get("amount")

		if amount is None:
			return {"success": False, "error": "Bid amount is required"}
		result = game.placeBid(playerId, amount)
	elif action == "passAuction":
		result = game.passAuction(playersId)
	elif action == "endTurn":
		result = game.endTurn(playersId)
	elif action == "mortgage":
		result = game.mortgage(playersId, params.get("position", -1))
	elif action == "build":
		result = game.buildHouse(playersId, params.get("position", -1))
	elif action == "jailPay":
		return self.payJailFine(gameId, playersId)
	elif action == "jailCard":
		return self.useJailCard(gameId, playersId)
	else:
		return {"success": False, "error": "Unknown action"}
	if result is False:
		return {"success": False, "error": "Unable to perform action"}
	return {"success": True, "result": result, "state": game.getState(playersId)}

@app.post("/games")
def createGame(request: CreateGameRequest):
	players = [
		Player(player.playerId, player.name)
		for player in request.players
	]
	board = loadBoard("board.json")
	success = server.createGame(request.gameId, players, board)
	if not success:
		return {
			"success": False,
			"error": "Game already exists"
		}
	return {
		"success": True,
		"gameId": request.gameId
	}

@app.post("/games/{gameId}/action")
async def doAction(gameId: str, req: ActionRequest):
    params = {}
    if req.position is None:
    	params["position"] = req.position
    if req.amount is not None:
    	params["amount"] = req.amount
    return server.act(gameId, req.playerId, req.action, **params)

# @app.post("/games/{gameId}/roll")
# def roll(gameId: str, request: RollRequest):
# 	result = server.roll(gameId, request.playerId)
# 	return result

# @app.post("/games/{gameId}/jail/pay")
# def payJailFine(gameId: str, request: RollRequest):
# 	return server.payJailFine(gameId, request.playerId)

# @app.post("/games/{gameId}/jail/card")
# def useJailCard(gameId: str, request: RollRequest):
# 	return server.useJailCard(gameId, request.playerId)

@app.get("/games/{gameId}/state/{playerId}")
def getGameState(gameId: str, playerId: int):
    return server.getState(gameId, playerId)