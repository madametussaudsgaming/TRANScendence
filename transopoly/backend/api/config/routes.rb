Rails.application.routes.draw do
  # Define your application routes per the DSL in https://guides.rubyonrails.org/routing.html

  # Reveal health status on /up that returns 200 if the app boots with no exceptions, otherwise 500.
  # Can be used by load balancers and uptime monitors to verify that the app is live.
  get "up" => "rails/health#show", as: :rails_health_check
  resources :game_sessions, only: [:index, :show, :create] do
    member do
      post  :join
      post  :leave
      post  :start
      post  :play
      get   :state
    end
  end
  resources :users, only: [:create]
  post    "/login", to: "sessions#create"
  delete  "/logout", to: "sessions#destroy"
end

# Defines the root path route ("/")
# root "posts#index"

# member routes include the game's id (/game_sessions/5/join).
# The other kind, collection routes, have no id (/game_sessions/something).
# Each of these actions works on one specific game, so member is the right choice
