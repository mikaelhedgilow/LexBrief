#!/usr/bin/env python3
import http.server
import json
import urllib.request
import urllib.error
import os

PORT = int(os.environ.get('PORT', 8765))
API_KEY_ENV = os.environ.get('ANTHROPIC_API_KEY', '')

class LexBriefHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/LexBrief.html')
            self.end_headers()
        else:
            super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        if self.path == '/api/analyze':
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)

            # Använd server-side nyckel om satt, annars klientens
            api_key = API_KEY_ENV or data.get('apiKey', '')
            text = data.get('text', '')
            system_prompt = data.get('systemPrompt', '')

            if not api_key:
                msg = json.dumps({'error': {'message': 'Ingen API-nyckel konfigurerad.'}}).encode()
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(msg)
                return

            payload = json.dumps({
                'model': 'claude-opus-4-8',
                'max_tokens': 1500,
                'system': system_prompt,
                'messages': [{'role': 'user', 'content': f'Sammanfatta följande dom:\n\n{text}'}]
            }).encode('utf-8')

            req = urllib.request.Request(
                'https://api.anthropic.com/v1/messages',
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01'
                }
            )

            try:
                with urllib.request.urlopen(req) as response:
                    result = response.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(result)
            except urllib.error.HTTPError as e:
                error_body = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(error_body)
            except Exception as e:
                msg = json.dumps({'error': {'message': str(e)}}).encode()
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(msg)

        elif self.path == '/api/has-key':
            result = json.dumps({'hasKey': bool(API_KEY_ENV)}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(result)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print(f'LexBrief körs på port {PORT}')
    with http.server.HTTPServer(('0.0.0.0', PORT), LexBriefHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nServer stoppad.')
