class GameSessionsController < ApplicationController
	def index
		render json: GameSession.all
	end

	def show
		game = GameSession.find(params[:id])

		render json: {
			id: game.id,
			status: game.status,
			pythonGameId: pythonGameId,
			players: game.gameSessionPlayers.map do |player| {
				userId: player.userId
				playerId: player.playerId
			}
			end
		}
	end

	def create
		game = GameSession.create!(hostId: params[:hostId], status: "waiting")
		render json: {
			success: true,
			gameId: game.id
		}
	end

	def roll
		game = GameSession.find(params[:id])
		result = PythonGameClient.new.roll(game.pythonGameId, params[:playerId])
		render json: result
	end
end

	