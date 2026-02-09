#!/usr/bin/env python3
"""
Simple web preview server for Sambar HUD
"""

import http.server
import socketserver
import webbrowser
import sys

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(get_html().encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def get_html():
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sambar HUD Preview - 2560x720</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            background: #000;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .wrapper {
            border: 3px solid #007AFF;
            box-shadow: 0 0 30px rgba(0,122,255,0.5);
        }
        .container {
            display: flex;
            width: 2560px;
            height: 720px;
            transform: scale(0.35);
            transform-origin: top center;
        }
        .panel {
            width: 1280px;
            height: 720px;
            display: flex;
            flex-direction: column;
            border-right: 3px solid #333;
        }
        .panel:last-child { border-right: none; }
        .header {
            background: #1a1a1a;
            color: white;
            padding: 20px;
            font-size: 32px;
            font-weight: bold;
            text-align: center;
            border-bottom: 3px solid #333;
        }
        .content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .entertainment-panel { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); }
        .carplay-panel { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .mode-buttons {
            display: flex;
            gap: 8px;
            padding: 8px;
            background: #2a2a2a;
            border-bottom: 3px solid #333;
        }
        .mode-btn {
            flex: 1;
            padding: 12px;
            background: #2a2a2a;
            color: white;
            border: 2px solid #444;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.2s;
        }
        .mode-btn:hover { background: #3a3a3a; border-color: #555; }
        .mode-btn.active { background: #007AFF; border-color: #0056CC; }
        .panel-content {
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            padding: 40px;
            text-align: center;
        }
        .info-box {
            background: rgba(0,0,0,0.6);
            padding: 30px;
            border-radius: 12px;
            max-width: 700px;
        }
        .info-box h2 {
            font-size: 36px;
            margin-bottom: 20px;
        }
        .info-box p {
            font-size: 20px;
            line-height: 1.6;
            margin-bottom: 15px;
        }
        .feature-list {
            list-style: none;
            margin-top: 20px;
            text-align: left;
        }
        .feature-list li {
            padding: 10px 0;
            padding-left: 30px;
            font-size: 18px;
            position: relative;
        }
        .feature-list li:before {
            content: "✓";
            position: absolute;
            left: 0;
            color: #0f0;
            font-weight: bold;
            font-size: 20px;
        }
        .carplay-status {
            background: #2a2a2a;
            color: #0f0;
            padding: 15px;
            text-align: center;
            font-size: 18px;
            margin: 20px 0;
            border-radius: 6px;
        }
        .connect-btn {
            background: #007AFF;
            color: white;
            border: none;
            padding: 18px 40px;
            font-size: 20px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .connect-btn:hover { background: #0056CC; }
        .status {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0,122,255,0.9);
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            font-weight: bold;
            z-index: 1000;
        }
    </style>
</head>
<body>
    <div class="status">Server Running - Port 8000</div>
    <div class="wrapper">
        <div class="container">
            <div class="panel entertainment-panel">
                <div class="header">Entertainment</div>
                <div class="content">
                    <div class="mode-buttons">
                        <button class="mode-btn active" onclick="switchMode('steam')">Steam Link</button>
                        <button class="mode-btn" onclick="switchMode('youtube')">YouTube</button>
                        <button class="mode-btn" onclick="switchMode('netflix')">Netflix</button>
                        <button class="mode-btn" onclick="switchMode('airplay')">AirPlay</button>
                    </div>
                    <div class="panel-content" id="ent-content">
                        <div class="info-box">
                            <h2>🎮 Steam Link</h2>
                            <p>Stream games from your PC directly to your car's display</p>
                            <ul class="feature-list">
                                <li>Low-latency streaming</li>
                                <li>Full controller support</li>
                                <li>High-quality graphics</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            <div class="panel carplay-panel">
                <div class="header">CarPlay</div>
                <div class="content">
                    <div class="panel-content">
                        <div class="info-box">
                            <h2>🍎 Apple CarPlay</h2>
                            <p>Connect your iPhone for navigation, music, and more</p>
                            <ul class="feature-list">
                                <li>Apple Maps navigation</li>
                                <li>Music & podcasts</li>
                                <li>Phone & messages</li>
                                <li>Siri voice control</li>
                            </ul>
                        </div>
                        <div class="carplay-status" id="status">Ready to connect</div>
                        <button class="connect-btn" onclick="connect()">Connect CarPlay</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
        const modes = {
            steam: { title: '🎮 Steam Link', desc: 'Stream games from your PC', features: ['Low-latency streaming', 'Full controller support', 'High-quality graphics'] },
            youtube: { title: '📺 YouTube', desc: 'Watch videos on the go', features: ['YouTube TV interface', 'Video recommendations', 'Playlist support'] },
            netflix: { title: '🎬 Netflix', desc: 'Stream movies and shows', features: ['Full Netflix library', 'HD/4K streaming', 'Download for offline'] },
            airplay: { title: '📱 AirPlay', desc: 'Stream from iPhone/iPad', features: ['Wireless streaming', 'Screen mirroring', 'Audio & video'] }
        };
        function switchMode(m) {
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            const d = modes[m];
            document.getElementById('ent-content').innerHTML = `<div class="info-box"><h2>${d.title}</h2><p>${d.desc}</p><ul class="feature-list">${d.features.map(f => '<li>'+f+'</li>').join('')}</ul></div>`;
        }
        function connect() {
            const s = document.getElementById('status');
            s.textContent = 'Connecting...';
            s.style.color = '#ff0';
            setTimeout(() => { s.textContent = 'CarPlay Connected ✓'; s.style.color = '#0f0'; }, 2000);
        }
    </script>
</body>
</html>"""

def main():
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            url = f"http://localhost:{PORT}"
            print(f"\n{'='*70}")
            print("🚗 Sambar HUD Preview Server")
            print(f"{'='*70}")
            print(f"\n✅ Server started successfully!")
            print(f"📍 URL: {url}")
            print(f"\n🌐 Opening in your browser...")
            print(f"\n⚠️  If it doesn't open automatically, copy this URL:")
            print(f"   {url}")
            print(f"\n⏹️  Press Ctrl+C to stop the server\n")
            
            try:
                webbrowser.open(url)
            except:
                print("(Could not auto-open browser)")
            
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"\n❌ Port {PORT} is already in use!")
            print(f"   Try: lsof -ti:{PORT} | xargs kill")
            print(f"   Or use a different port\n")
        else:
            print(f"\n❌ Error: {e}\n")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped.\n")

if __name__ == "__main__":
    main()
