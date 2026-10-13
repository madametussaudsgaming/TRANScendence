class SessionsController < ApplicationController:
	def create
		user = User.find_by(email: params[:email])
		if user&.authenticate(params[:password])
			session[:userId] = user.id
			render json: {
				success: true,
				user: {
					id: user.id,
					email: user.email
				}
			}
		else
			render json: {
				success: false,
				error: "Invalid email or password"
			}, status: :unauthorized
		end
	end

	def destroy
		reset_session
		render json: {
			success: true
		}
	end
end