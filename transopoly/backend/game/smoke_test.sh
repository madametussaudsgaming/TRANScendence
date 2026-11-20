#!/usr/bin/env bash
# Quick check that the game engine container works.
# Usage: ./smoke_test.sh            (defaults to http://127.0.0.1:8000)
#        ./smoke_test.sh http://host:port
set -euo pipefail
URL="${1:-http://127.0.0.1:8000}"
GAME="smoke-$(date +%s)"

echo "1) Create game $GAME"
curl -sf -X POST "$URL/games" -H "Content-Type: application/json" \
  -d "{\"gameId\":\"$GAME\",\"players\":[{\"playerId\":1,\"name\":\"Alice\"},{\"playerId\":2,\"name\":\"Bob\"}]}"
echo

echo "2) Player 1 rolls"
curl -sf -X POST "$URL/games/$GAME/action" -H "Content-Type: application/json" \
  -d '{"playerId":1,"action":"roll"}' | python3 -c "import sys,json; r=json.load(sys.stdin); print('success:', r['success'], '| result:', r.get('result', r.get('error')))"

echo "3) Player 2 tries to roll (should be refused with success:false)"
curl -sf -X POST "$URL/games/$GAME/action" -H "Content-Type: application/json" \
  -d '{"playerId":2,"action":"roll"}'
echo

echo "4) State for player 1"
curl -sf "$URL/games/$GAME/state/1" | python3 -c "import sys,json; s=json.load(sys.stdin)['state']; print('turn:', s['currentTurn'], '| position:', s['player']['position'], '| money:', s['player']['money'])"

echo "All requests answered."