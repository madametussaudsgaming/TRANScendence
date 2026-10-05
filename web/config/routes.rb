Rails.application.routes.draw do
	resources :gameSessions, only: [:index, :show, :create] do
		post :roll, on, :member
		delete :leave, on: :member
		post :start, on: :member
		post :roll, on: :member
	end
end