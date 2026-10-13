Rails.application.routes.draw do
	post "/login", to: "sessions#create"
	delete "/logout", to: "sessions#destroy"
	resources :gameSessions, only: [:index, :show, :create] do
		post :roll, on, :member
		delete :leave, on: :member
		post :start, on: :member
		post :roll, on: :member
	end
end