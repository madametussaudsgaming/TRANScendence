from fastapi import FastAPI
from pydantic import BaseModel
from board import loadBoard
from engine import GameServer, Player

app = FastAPI()
server = GameServer()

class PlayerData(BaseModel):
	playerId: int
	name: str

class CreateGameRequest(BaseModel):
	gameId: str
	players: list[PlayerData]

class RollRequest(BaseModel):
	playerId: int

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

@app.post("/games/{gameId}/roll")
def roll(gameId: str, request: RollRequest):
	result = server.roll(gameId, request.playerId)
	return result