require "net/http"
require "json"

# Talks to the FastAPI game engine. Every public method returns a Hash with
# string keys and always has a "success" key, even when the engine is down,
# so controllers can just check result["success"].
class PythonGameClient
	BASE_URL = ENV.fetch("PYTHON_GAME_SERVER_URL", "http://game:8000")
	OPEN_TIMEOUT = 2 # seconds to wait for the connection
	READ_TIMEOUT = 5 # seconds to wait for the answer

	# Errors that mean "the engine couldn't be reached or answered garbage"
	NETWORK_ERRORS = [
		Net::OpenTimeout, Net::ReadTimeout,
		Errno::ECONNREFUSED, Errno::ECONNRESET, Errno::EHOSTUNREACH,
		SocketError, JSON::ParserError
	].freeze

	def create_game(game_id, players)
		request(:post, "/games", { gameId: game_id, players: players })
	end

	# fields comes from the controller's permitted params, e.g.
	# { "action" => "buy", "position" => 3 }. playerId is set here, from
	# the server side, after the fields, so it can never be overridden.
	def act(game_id, player_id, fields)
		request(:post, "/games/#{game_id}/action", fields.to_h.merge("playerId" => player_id))
	end

	def state(game_id, player_id)
		request(:get, "/games/#{game_id}/state/#{player_id}")
	end

	private

	def request(method, path, body = nil)
		uri = URI.join(BASE_URL, path)
		req = (method == :post ? Net::HTTP::Post : Net::HTTP::Get).new(uri)
		if body
			req["Content-Type"] = "application/json"
			req.body = body.to_json
		end

		response = Net::HTTP.start(uri.host, uri.port,
			open_timeout: OPEN_TIMEOUT, read_timeout: READ_TIMEOUT) do |http|
			http.request(req)
		end

		parsed = response.body.present? ? JSON.parse(response.body) : {}

		unless response.is_a?(Net::HTTPSuccess)
			return {
				"success" => false,
				"error" => "Engine rejected request (HTTP #{response.code})",
				"details" => parsed
			}
		end

		# The state endpoint may not include "success"; treat a 2xx as success
		parsed.is_a?(Hash) ? { "success" => true }.merge(parsed) : { "success" => true, "data" => parsed }
	rescue *NETWORK_ERRORS => e
		Rails.logger.error("[PythonGameClient] #{method.upcase} #{path} failed: #{e.class}: #{e.message}")
		{ "success" => false, "error" => "Game engine unavailable" }
	end
end
