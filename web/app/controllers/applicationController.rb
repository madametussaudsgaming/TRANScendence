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
		end
	end
end