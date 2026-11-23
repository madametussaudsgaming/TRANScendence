class GameSessionsController < ApplicationController
	before_action :require_login
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
				userId: player.user_id,
				playerId: player.player_id
			}
			end
		}
	end

	def create
		GameSession.transaction do
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
	end
	

	def join
		game = GameSession.find(params[:id])
		unless game.waiting?
			return render json: {
				success: false,
				error: "Game has already started"
			}, status: :unprocessable_content
		end

		if game.full?
			return render json: {
				success: false,
				error: "Game is full"
			}, status: :unprocessable_content
		end

		if game.players.exists?(current_user.id)
			return render json: {
				success: false,
				error: "Already in game"
			}, status: :unprocessable_content
		end

		# mutex time!
		game.with_lock do
			next_player_id = game.game_session_players.maximum(:player_id).to_i + 1
			player = game.game_session_players.create!(
				user_id: current_user.id,
				player_id: next_player_id
			)
			render json: {
				success: true,
				playerId: player.player_id
			}
		end
	end

	def leave
		game = GameSession.find(params[:id])

		return unless require_player(game)

		unless game.waiting?
			return render json: {
				success: false,
				error: "Players cannot leave after the game starts"
			}, status: :unprocessable_content
		end

		if game.host_id == current_user.id
			return render json: {
				success: false,
				error: "The host cannot leave. Delete the lobby or transfer first"
			}, status: :unprocessable_content
		end

		player = game.game_session_players.find_by(user_id: current_user.id)
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
			}, status: :unprocessable_content
		end

		players = game.game_session_players.map do |player| {
			playerId: player.player_id,
			name: player.user.email
		}
		#sent to pythone engine, uses playerId
		end
		if players.size < 2
			return render json: { success: false, error: "Need at least 2 players" }, status: :unprocessable_content
		end

		python_game_id = "game-#{game.id}-#{SecureRandom.hex(4)}"
		result = PythonGameClient.new.create_game(python_game_id, players)
		unless result["success"]
			return render json: {
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
	end

	ENGINE_FIELDS = [:position, :amount, :tradeId, :toPlayerId, :offerMoney, :requestMoney,
						:offerJailCards, :requestJailCards, { offerProperties: [], requestProperties: [] }]

	def play
		game = GameSession.find(params[:id])
		return unless require_player(game)

		player = game.game_session_players.find_by(user_id: current_user.id)
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