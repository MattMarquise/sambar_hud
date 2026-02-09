#!/usr/bin/env python3
"""
Web-based preview of Sambar HUD
Runs a local web server so you can see the layout in your browser
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 8080

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sambar HUD Preview</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            overflow: hidden;
            background: #000;
        }
        
        .container {
            display: flex;
            width: 2560px;
            height: 720px;
            margin: 0 auto;
            transform: scale(0.5);
            transform-origin: top left;
            border: 2px solid #333;
        }
        
        .panel {
            width: 1280px;
            height: 720px;
            display: flex;
            flex-direction: column;
            border-right: 2px solid #333;
        }
        
        .panel:last-child {
            border-right: none;
        }
        
        .header {
            background: #1a1a1a;
            color: white;
            padding: 15px;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            border-bottom: 2px solid #333;
        }
        
        .content {
            flex: 1;
            background: #000;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        /* Entertainment Panel Styles */
        .entertainment-panel {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        }
        
        .mode-buttons {
            display: flex;
            gap: 5px;
            padding: 5px;
            background: #2a2a2a;
            border-bottom: 2px solid #333;
        }
        
        .mode-btn {
            flex: 1;
            padding: 10px;
            background: #2a2a2a;
            color: white;
            border: 2px solid #444;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
            transition: all 0.3s;
        }
        
        .mode-btn:hover {
            background: #3a3a3a;
            border-color: #555;
        }
        
        .mode-btn.active {
            background: #007AFF;
            border-color: #0056CC;
        }
        
        .entertainment-content {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 18px;
            text-align: center;
            padding: 20px;
        }
        
        /* CarPlay Panel Styles */
        .carplay-panel {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        .carplay-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
            padding: 20px;
        }
        
        .carplay-status {
            background: #2a2a2a;
            color: #0f0;
            padding: 10px;
            text-align: center;
            font-size: 14px;
            margin-top: 10px;
        }
        
        .connect-btn {
            background: #007AFF;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 20px;
            transition: background 0.3s;
        }
        
        .connect-btn:hover {
            background: #0056CC;
        }
        
        .info-box {
            background: rgba(0, 0, 0, 0.5);
            padding: 20px;
            border-radius: 10px;
            max-width: 600px;
            margin: 20px;
        }
        
        .info-box h2 {
            margin-bottom: 15px;
            font-size: 28px;
        }
        
        .info-box p {
            margin-bottom: 10px;
            line-height: 1.6;
            font-size: 16px;
        }
        
        .feature-list {
            list-style: none;
            padding-left: 0;
            margin-top: 15px;
        }
        
        .feature-list li {
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
        }
        
        .feature-list li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #0f0;
            font-weight: bold;
        }
        
        @media (max-width: 1400px) {
            .container {
                transform: scale(0.4);
            }
        }
        
        @media (max-width: 1100px) {
            .container {
                transform: scale(0.3);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Left Panel: Entertainment -->
        <div class="panel entertainment-panel">
            <div class="header">Entertainment</div>
            <div class="content">
                <div class="mode-buttons">
                    <button class="mode-btn active" onclick="switchMode('steam')">Steam Link</button>
                    <button class="mode-btn" onclick="switchMode('youtube')">YouTube</button>
                    <button class="mode-btn" onclick="switchMode('netflix')">Netflix</button>
                    <button class="mode-btn" onclick="switchMode('airplay')">AirPlay</button>
                </div>
                <div class="entertainment-content" id="entertainment-content">
                    <div class="info-box">
                        <h2>Steam Link</h2>
                        <p>Connect to your gaming PC and stream games directly to your car's display.</p>
                        <ul class="feature-list">
                            <li>Low-latency game streaming</li>
                            <li>Full controller support</li>
                            <li>High-quality graphics</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Right Panel: CarPlay -->
        <div class="panel carplay-panel">
            <div class="header">CarPlay</div>
            <div class="content">
                <div class="carplay-content">
                    <div class="info-box">
                        <h2>Apple CarPlay</h2>
                        <p>Connect your iPhone for maps, music, messages, and more.</p>
                        <ul class="feature-list">
                            <li>Apple Maps navigation</li>
                            <li>Music and podcast playback</li>
                            <li>Phone calls and messages</li>
                            <li>Siri voice control</li>
                        </ul>
                    </div>
                    <div class="carplay-status" id="carplay-status">Ready to connect</div>
                    <button class="connect-btn" onclick="connectCarPlay()">Connect CarPlay</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function switchMode(mode) {
            // Update button states
            document.querySelectorAll('.mode-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Update content
            const content = document.getElementById('entertainment-content');
            const modes = {
                steam: {
                    title: 'Steam Link',
                    desc: 'Connect to your gaming PC and stream games directly to your car\'s display.',
                    features: ['Low-latency game streaming', 'Full controller support', 'High-quality graphics']
                },
                youtube: {
                    title: 'YouTube',
                    desc: 'Watch your favorite videos and channels on the go.',
                    features: ['YouTube TV interface', 'Video recommendations', 'Playlist support']
                },
                netflix: {
                    title: 'Netflix',
                    desc: 'Stream movies and TV shows during long drives.',
                    features: ['Full Netflix library', 'HD/4K streaming', 'Download for offline viewing']
                },
                airplay: {
                    title: 'AirPlay',
                    desc: 'Stream content directly from your iPhone or iPad.',
                    features: ['Wireless streaming', 'Screen mirroring', 'Audio and video support']
                }
            };
            
            const modeData = modes[mode];
            content.innerHTML = `
                <div class="info-box">
                    <h2>${modeData.title}</h2>
                    <p>${modeData.desc}</p>
                    <ul class="feature-list">
                        ${modeData.features.map(f => `<li>${f}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        function connectCarPlay() {
            const status = document.getElementById('carplay-status');
            status.textContent = 'Connecting...';
            status.style.color = '#ff0';
            
            setTimeout(() => {
                status.textContent = 'CarPlay Connected';
                status.style.color = '#0f0';
            }, 2000);
        }
    </script>
</body>
</html>
"""

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())
        else:
            super().do_GET()

def main():
    """Start the web server"""
    os.chdir(Path(__file__).parent)
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print(f"\n{'='*60}")
        print("Sambar HUD Preview Server")
        print(f"{'='*60}")
        print(f"\nServer running at: {url}")
        print("\nOpening in your browser...")
        print("\nPress Ctrl+C to stop the server\n")
        
        # Try to open browser
        try:
            webbrowser.open(url)
        except:
            pass
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")

if __name__ == "__main__":
    main()
