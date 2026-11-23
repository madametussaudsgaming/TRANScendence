class User < ApplicationRecord
	has_secure_password
	has_many :game_session_players, dependent: :destroy
	has_many :game_sessions, through: :game_session_players
	normalizes :email, with: ->(e) { e.strip.downcase }
	validates :email, presence: true, uniqueness: true
end