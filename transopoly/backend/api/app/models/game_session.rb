class GameSession < ApplicationRecord
	belongs_to :host,
				class_name: "User"
	has_many :game_session_players,
			dependent: :destroy
	has_many :players, through: :game_session_players, source: :user
	# Why source: :user? players tells Rails to look for an
	# association called player on GameSessionPlayer, but
	# that association is called user. source: tells it which
	# one to use.

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