class GameSession < ApplicationRecord
	belongs_to :host,
				className: "User",
				foreignKey: :hostId
	has_many :gameSessionPlayers,
			dependent: :destory
	has_many :players,
			through: :gameSessionPlayers
	validates :status, inclusion: {
		in: %w[waiting starting playing finished]
	}

	def waiting?
		status == "waiting"
	end

	def playing?
		status == "playing"
	end

	def full?
		players.count >= 4
	end
end