class UsersController < ApplicationController
	def create
		user = User.new(
			email: params[:email],
			password: params[:password],
			password_confirmation: params[:password_confirmation]
		)
		if user.save
			render json: {
				success: true,
				user: {
					id: user.id,
					email: user.email
				}
			}, status: :created
		else
			render json: {
				success: false,
				errors: user.errors.full_messages
			}, status: :unprocessableEntity
		end
	end
end