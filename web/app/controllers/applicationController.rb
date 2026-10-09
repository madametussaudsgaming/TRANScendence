class ApplicationController < ActionController::Base
	private
	def current_user
		return nil unless session[:user_id]
		User.find_by(id: session[:user_id])
	end

	def require_login
		unless current_user
			render json: {
				success: false,
				error: "You must be logged in"
			}, status: :unauthorized
			return false
		end
		true
	end

	def require_host(game)
		unless game.host_id == current_user.id
			render json: {
				success: false,
				error: "This requires the host to do this task"
			}, status:
			return false
		end
		true
	end

	def require_player(game)
		unless game.game_session_players.exist?(
			user_id: current_user.id
		)
			render json: {
				success: false,
				error: "You are not a player"
			}, status: :forbidden
			return false
		end
		true
	end
end