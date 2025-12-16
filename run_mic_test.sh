#!/bin/bash
# Script to run microphone test with HTTP server

echo "Starting HTTP server for microphone test..."
cd "$(dirname "$0")"

# Kill any existing server on port 8080
lsof -ti:8080 | xargs kill -9 2>/dev/null

# Start HTTP server in background
python3 -m http.server 8080 > /tmp/mic_test_server.log 2>&1 &
SERVER_PID=$!

echo "HTTP server started (PID: $SERVER_PID)"
echo ""
echo "Opening test page in browser..."
sleep 1

# Open in browser
open http://localhost:8080/test_microphone.html

echo ""
echo "✅ Test page opened at: http://localhost:8080/test_microphone.html"
echo ""
echo "⚠️  IMPORTANT: Your microphone shows as 'Muted: true'"
echo "   Please check:"
echo "   1. System Settings → Sound → Input"
echo "   2. Make sure microphone is not muted"
echo "   3. Check browser microphone permissions"
echo ""
echo "Press Ctrl+C to stop the server when done"
echo ""

# Wait for user to stop
trap "kill $SERVER_PID 2>/dev/null; echo 'Server stopped.'; exit" INT TERM
wait $SERVER_PID

