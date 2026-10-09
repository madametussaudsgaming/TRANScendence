class GameSessionsController < ApplicationController
	before_action: :require_login
	def index
		render json: GameSession.all
	end

	def show
		game = GameSession.find(params[:id])

		return unless require_player(game)
		render json: {
			id: game.id,
			status: game.status,
			pythonGameId: game.python_game_id,
			players: game.game_session_players.map do |player| {
				userId: player.user_id
				playerId: player.player_id
			}
			end
		}
	end

	def create
		game = GameSession.create!(
			host_id: current_user.id,
			status: "waiting"
		)
		game.game_session_players.create!(
			user_id: current_user.id,
			player_id: 1
		)
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
			}, status: :unprocessable_entity
		end

		if game.full?
			return render json: {
				success: false,
				error: "Game is full"
			}, status: :unprocessable_entity
		end

		if game.players.exists?(current_user.id)
			return render json: {
				success: false,
				error: "Already in game"
			}, status: :unprocessable_entity
		end

		next_player_id = game.game_session_players.maximum(:playerId).to_i + 1
		player = game.game_session_players.create!(
			userId: current_user.id,
			playerId: next_player_id
		)
		render json: {
			success: true,
			playerId: player.player_id
		}
	end

	def leave
		game = GameSession.find(params[:id])
		player = game.game_session_players.find_by(user_id: current_user.id)
		
		unless player
			return render json: {
				success: false,
				error: "Player is not in this game"
			}, status: :not_found
		end

		player.destroy!
		render json: {
			success: true
		}
	end

	def start
		game = GameSession.find(params[:id])
		
		return unless require_host(game)
		unless game.waiting?
			return render json: {
				success: false,
				error: "Game cannot be started"
			}, status: :unprocessable_entity
		end

		players = game.game_session_players.map do |player| {
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

    	return unless require_player(game)
		player = game.game_session_players.find_by(userId: current_user.id)
		unless player
			return render json: {
				success: false,
				error: "Player not found"
			}, status: :forbidden
		end
    	result = PythonGameClient.new.roll(
			game.python_game_id,
			player.player_id
		)
		render json: result
	end
end