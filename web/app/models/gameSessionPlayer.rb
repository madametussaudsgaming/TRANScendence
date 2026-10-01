class GameSessionPlayer < ApplicationRecord
	belongs_to :gameSession
	belongs_to :user
	validates :playerId, presense: true
end