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
		game.with_lock do

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
	
	# player_id is our databases version of the players seat number

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
		game.with_lock do
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
			# camelCase rule only applies to JSON keys
			render json: {
				success: true,
				gameId: game.id,
				pythonGameId: python_game_id
			}
		end
	end

	ENGINE_FIELDS = [:position, :amount, :tradeId, :toPlayerId, :offerMoney, :requestMoney,
						:offerJailCards, :requestJailCards, { offerProperties: [], requestProperties: [] }]


	def play
		game, player = find_active_player
		# i use a returned array so that if find_active_player returns nil, both game and player become nil
		return unless player

		fields = params.require(:game_action).permit(:action, *ENGINE_FIELDS)
		#  If the wrapper is missing, the request is rejected with a 400.
		result = PythonGameClient.new.act(game.python_game_id, player.player_id, fields)
		render json: result, status: engine_status(result)
	end
	# fails with a 400 if the client forgot the wrapper.
	#permit lets through only action plus the fields
	#listed in ENGINE_FIELDS. Anything else like fakeing
	#playerId, is dropped.

	def state
		game, player = find_active_player
		return unless player

		result = PythonGameClient.new.state(game.python_game_id, player.player_id)
		render json: result, status: engine_status(result)
	end

	private

	def find_active_player
		game = GameSession.find(params[:id])
		return unless require_player(game)

		unless game.playing?
			render json: {
				success: false,
				error: "Game is not in progress"
			}, status: :unprocessable_content
			return
		end

		return [game, game.game_session_players.find_by!(user_id: current_user.id)]
	end

	def engine_status(result)
		return :ok if result["success"]
		result["error"] == "Game engine unavailable" ? :bad_gateway : :unprocessable_content
	end
end