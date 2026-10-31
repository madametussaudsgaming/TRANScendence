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
    action: Literal["roll", "buy", "decline", "endTurn", "mortgage", "build", "jailPay", "jailCard"]
    position: Optional[int] = None

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
    params = {} if req.position is None else {"position": req.position}
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