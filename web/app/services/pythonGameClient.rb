require "net/http"
require "json"
require "uri"

class PythonGameClient
	def initialize
		@base_url = ENV.fetch(
			"PYTHON_GAME_SERVER_URL",
			"http://127.0.0.1:8000"
		)
	end

	def createGame(gameId, players)
		post("/games", {
			gameId: gameId,
			players: players
		})
	end

	def roll(gameId, playerId)
		post("/games/#{gameId}/roll", {
			playerId: playerId
		})
	end

	private
	def post(path, body)
		uri = URI("#{@base_url}#{path}")

		request = Net::HTTP::Post.new(uri)
		request["Content-Type"] = "application/json"
		request.body = JSON.generate(body)

		response = Net::HTTP.start(uri.hostname, uri.port) do |http| http.request(request)
		end

	JSON.parse(response.body)
	end
end