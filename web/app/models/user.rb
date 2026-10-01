class User < ApplicationRecord
	has_secure_password
	has_many :gameSessionPlayers, dependent: :destroy
	has_many :gameSessions,
			through: :gameSessionPlayers
end