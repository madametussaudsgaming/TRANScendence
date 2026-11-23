class GameSessionPlayer < ApplicationRecord
	belongs_to :game_session
	belongs_to :user
	validates :player_id, presence: true
end