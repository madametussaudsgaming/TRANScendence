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
		game.gameSessionPlayers.create!(userId: params[:hostId], player_id: 1)
		render json: {
			success: true,
			gameId: game.id
		}
	end

	def join
		game = GameSession.find(params[:id])
		unless game.waiting?
			return render json: {
				success: false,
				error: "Game has already started"
			}, status: :unprocessableEntity
		end

		if game.full?
			return render json: {
				success: false,
				error: "Game is full"
			}, status: :unprocessableEntity
		end

		if game.players.exists?(params[:userId])
			return render json: {
				success: false,
				error: "Already in game"
			}, status: :unprocessableEntity
		end

		nextPlayerId = game.gameSessionPlayers.maximum(:playerId).to_i + 1
		player = game.gameSessionPlayers.create!(userId: params[:userId], playerId: nextPlayerId)
		render json: {
			success: true,
			playerId: player.playerId
		}
	end

	def leave
		game = GameSession.find(params[:id])
		player = game.gameSessionPlayers.find_by(userId: params[:userId])
		
		unless player
			return render json: {
				success: false,
				error: "Player is not in this game"
			}, status: :not_found
		end

		player.destory!
		render json: {success: true}
	end

	def start
		game = GameSession.find(params[:id])
		unless game.waiting?
			return render json: {
				success: false,
				error: "Game cannot be started"
			}, status: :unprocessableEntity
		end

		players = game.gameSessionPlayers.map do |player| {
			playerId: player.player_id,
			name: player.user.email
		}
		end

		python_game_id = "game-#{game.id}-#{SecureRandom.hex(4)}"
		result = PythonGameClient.new.create_game(python_game_id, players)
		unless result["success"]
			return result json: {
				success: false,
				error: "Python server failed to create a game",
				details: result
			}, status: :bad_gateway
		end
	
		game.update!(
			status: "playing",
			python_game_id: python_game_id
		)

		render json: {
			success: true,
			gameId: game.id,
			python_game_id: python_game_id
		}

	def roll
    	game = GameSession.find(params[:id])
    	result = PythonGameClient.new.roll(game.python_game_id, params[:player_id])
		render json: result
	end
end

	