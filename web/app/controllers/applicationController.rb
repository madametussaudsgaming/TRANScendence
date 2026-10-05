class ApplicationController < ActionController::Base
	private
	def current_user
		return nil unless session[:userId]
		User.find_by(id: session[:userId])
	end

	def requireLogin
		unless current_user
			render json: {
				success: false,
				error: "You must be logged in"
			}, status: :unauthorized
		end
	end
end