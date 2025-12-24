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
            # Validate authorization header format before parsing
            if not auth_header:
                self.send_error(401, "Missing Authorization header")
                return
            if not auth_header.startswith("Bearer "):
                self.send_error(401, "Invalid Authorization format (expected 'Bearer <token>')")
                return
            if len(auth_header) <= 7:
                self.send_error(401, "Empty bearer token")
                return
            if auth_header[7:] != self.auth_token:
                self.send_error(401, "Invalid token")
                return

        # Read request body with validation
        try:
            content_length_str = self.headers.get("Content-Length", "0")
            content_length = int(content_length_str)
            if content_length < 0:
                self.send_error(400, "Invalid Content-Length: negative value")
                return
            if content_length > 10 * 1024 * 1024:  # 10MB limit
                self.send_error(413, "Request body too large (max 10MB)")
                return
        except ValueError:
            self.send_error(400, f"Invalid Content-Length header: '{content_length_str}'")
            return

        try:
            body = self.rfile.read(content_length)
        except IOError as e:
            self.send_error(500, f"Error reading request body: {e}")
            return

        try:
            decoded_body = body.decode("utf-8")
        except UnicodeDecodeError as e:
            self.send_error(400, f"Invalid UTF-8 encoding in request body: {e}")
            return

        try:
            data = json.loads(decoded_body)
            if not isinstance(data, dict):
                self.send_error(400, "Request body must be a JSON object")
                return

            self.process_logs(data)

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {"status": "ok", "received": data.get("count", 0)}
            self.wfile.write(json.dumps(response).encode())

        except json.JSONDecodeError as e:
            self.send_error(400, f"Invalid JSON: {e}")
        except IOError as e:
            self.send_error(500, f"I/O error processing logs: {e}")
        except Exception as e:
            self.send_error(500, f"Server error: {e}")

    def process_logs(self, data):
        """Process and store received logs.

        Args:
            data: Dictionary containing session, symbol, and logs

        Raises:
            IOError: If logs cannot be written to file
            OSError: If output directory cannot be created
        """
        # Validate and sanitize input data
        session = str(data.get("session", "unknown"))[:64]  # Limit length
        symbol = str(data.get("symbol", "unknown"))[:32]  # Limit length
        logs = data.get("logs", [])

        # Sanitize session and symbol for use in filename (remove invalid chars)
        safe_session = "".join(c for c in session if c.isalnum() or c in "-_")
        safe_symbol = "".join(c for c in symbol if c.isalnum() or c in "-_")

        if not isinstance(logs, list):
            print(f"[{datetime.now().isoformat()}] Warning: 'logs' field is not a list, skipping")
            return

        # Create output directory with error handling
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise IOError(f"Cannot create output directory (permission denied): {self.output_dir}") from e
        except OSError as e:
            raise IOError(f"Cannot create output directory: {self.output_dir} - {e}") from e

        # Generate filename
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = self.output_dir / f"quantum_{safe_symbol}_{safe_session}_{date_str}.jsonl"

        # Append logs to file (JSONL format) with proper error handling
        try:
            with open(filename, "a", encoding="utf-8") as f:
                for log_entry in logs:
                    try:
                        if isinstance(log_entry, str):
                            f.write(log_entry + "\n")
                        elif isinstance(log_entry, dict):
                            f.write(json.dumps(log_entry) + "\n")
                        else:
                            # Convert other types to string representation
                            f.write(json.dumps(str(log_entry)) + "\n")
                    except (TypeError, ValueError) as e:
                        # Log entry couldn't be serialized, skip it
                        print(f"  Warning: Could not serialize log entry: {e}")
                        continue
        except PermissionError as e:
            raise IOError(f"Cannot write to log file (permission denied): {filename}") from e
        except IOError as e:
            raise IOError(f"Error writing to log file: {filename} - {e}") from e

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
                except json.JSONDecodeError:
                    print(f"  {log_entry}")
            elif isinstance(log_entry, dict):
                level = log_entry.get("level", "INFO")
                message = log_entry.get("message", str(log_entry))
                ts = log_entry.get("ts", "")
                print(f"  [{level}] {ts} | {message}")
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

    # Validate port range
    if args.port < 1 or args.port > 65535:
        print(f"Error: Invalid port number {args.port}. Must be between 1 and 65535.")
        return 1

    # Validate and set output directory
    try:
        output_path = Path(args.output)
        LogReceiverHandler.output_dir = output_path
    except Exception as e:
        print(f"Error: Invalid output path '{args.output}': {e}")
        return 1

    # Create server with error handling for port binding
    try:
        server = HTTPServer((args.host, args.port), LogReceiverHandler)
    except PermissionError:
        print(f"Error: Permission denied binding to {args.host}:{args.port}")
        print("  - Try a port >= 1024 for non-root users")
        print("  - Or run with elevated privileges")
        return 1
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"Error: Port {args.port} is already in use")
            print("  - Try a different port with --port <number>")
            print("  - Or stop the other service using this port")
        else:
            print(f"Error: Cannot bind to {args.host}:{args.port}: {e}")
        return 1

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
    except Exception as e:
        print(f"\nServer error: {e}")
        server.shutdown()
        return 1

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main() or 0)
