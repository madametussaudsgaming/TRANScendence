from engine import GameServer
from engine import Player
from board import loadBoard

if __name__ == "__main__":
    server = GameServer()

    players = [
        Player(1, "Alex"),
        Player(2, "Bob")
    ]

    # Assuming you already loaded your board
    board = loadBoard("board.json")

    server.createGame("test123", players, board)

    result = server.roll("test123", 1)

    print(result)