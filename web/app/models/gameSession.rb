class GameSession < ApplicationRecord
	belongs_to :host,
				className: "User",
				foreignKey: :hostId
	has_many :gameSessionPlayers,
			dependent: :destory
	has_many :players,
			through: :gameSessionPlayers
end