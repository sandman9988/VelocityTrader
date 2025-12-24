#!/usr/bin/env python3
"""
Project Quantum - Log Receiver Server
Receives logs from MT5 EA webhook and stores them for review.

Usage:
    python log_receiver.py [--port 8080] [--output logs/]

For GitHub Actions, use with ngrok or similar for public endpoint.
"""

import argparse
import json
import os
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path


class LogReceiverHandler(BaseHTTPRequestHandler):
    output_dir = Path("logs")
    auth_token = os.environ.get("LOG_AUTH_TOKEN", "")

    def do_POST(self):
        # Check authorization if token is set
        if self.auth_token:
            auth_header = self.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer ") or auth_header[7:] != self.auth_token:
                self.send_error(401, "Unauthorized")
                return

        # Read request body
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode("utf-8"))
            self.process_logs(data)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"status": "ok", "received": data.get("count", 0)}
            self.wfile.write(json.dumps(response).encode())

        except json.JSONDecodeError as e:
            self.send_error(400, f"Invalid JSON: {e}")
        except Exception as e:
            self.send_error(500, f"Server error: {e}")

    def process_logs(self, data):
        """Process and store received logs."""
        session = data.get("session", "unknown")
        symbol = data.get("symbol", "unknown")
        logs = data.get("logs", [])

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = self.output_dir / f"quantum_{symbol}_{session}_{date_str}.jsonl"

        # Append logs to file (JSONL format)
        with open(filename, "a") as f:
            for log_entry in logs:
                if isinstance(log_entry, str):
                    f.write(log_entry + "\n")
                else:
                    f.write(json.dumps(log_entry) + "\n")

        # Print summary to console
        print(f"[{datetime.now().isoformat()}] Received {len(logs)} logs from {symbol} session {session}")

        # Print logs in real-time for review
        for log_entry in logs:
            if isinstance(log_entry, str):
                try:
                    parsed = json.loads(log_entry)
                    level = parsed.get("level", "INFO")
                    message = parsed.get("message", "")
                    ts = parsed.get("ts", "")
                    print(f"  [{level}] {ts} | {message}")
                except:
                    print(f"  {log_entry}")
            else:
                print(f"  {log_entry}")

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def main():
    parser = argparse.ArgumentParser(description="Project Quantum Log Receiver")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument("--output", type=str, default="logs", help="Output directory")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    LogReceiverHandler.output_dir = Path(args.output)

    server = HTTPServer((args.host, args.port), LogReceiverHandler)
    print(f"Log receiver listening on {args.host}:{args.port}")
    print(f"Logs will be stored in: {args.output}/")

    if LogReceiverHandler.auth_token:
        print("Authentication: ENABLED (LOG_AUTH_TOKEN set)")
    else:
        print("Authentication: DISABLED (set LOG_AUTH_TOKEN env var to enable)")

    print("\nWaiting for logs from MT5 EA...")
    print("-" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
