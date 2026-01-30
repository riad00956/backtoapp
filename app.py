import os
import subprocess
import threading
from flask import Flask, render_template_string, request, session
from flask_socketio import SocketIO

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev_secret_123'
socketio = SocketIO(app, cors_allowed_origins="*")

PASSWORD = "admin"  # আপনার পাসওয়ার্ড
PROJECT_DIR = "my_projects"

if not os.path.exists(PROJECT_DIR):
    os.makedirs(PROJECT_DIR)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Python Cloud IDE</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root { --bg: #0d1117; --card: #161b22; --border: #30363d; --text: #c9d1d9; --accent: #238636; --terminal: #000000; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
        .container { max-width: 1000px; margin: auto; }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 10px; margin-bottom: 20px; }
        .card { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        input, textarea { background: #0d1117; color: white; border: 1px solid var(--border); padding: 12px; border-radius: 6px; width: 100%; box-sizing: border-box; font-family: 'Fira Code', monospace; margin-bottom: 15px; }
        textarea { height: 250px; resize: vertical; }
        .btn { background: var(--accent); color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-weight: 600; transition: 0.3s; }
        .btn:hover { opacity: 0.8; }
        #terminal { background: var(--terminal); color: #00ff00; height: 300px; overflow-y: auto; padding: 15 font-family: 'Fira Code', monospace; border-radius: 6px; border: 1px solid var(--border); font-size: 13px; line-height: 1.5; }
        .terminal-input-group { display: flex; gap: 10px; margin-top: 10px; }
        .login-box { max-width: 400px; margin: 100px auto; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        {% if not logged_in %}
            <div class="card login-box">
                <h2>Access Portal</h2>
                <form method="POST">
                    <input type="password" name="password" placeholder="Enter System Password" required>
                    <button type="submit" class="btn" style="width:100%">Unlock Terminal</button>
                </form>
            </div>
        {% else %}
            <div class="header">
                <h2>Python Web IDE <span>●</span></h2>
                <span style="color: #8b949e;">Status: Online</span>
            </div>

            <div class="card">
                <input type="text" id="filename" placeholder="filename.py (e.g. main.py)">
                <textarea id="code" placeholder="# Paste your Python code here..."></textarea>
                <button onclick="runCode()" class="btn">🚀 Save & Deploy Project</button>
            </div>

            <div class="card">
                <h3 style="margin-top:0">Live Logs & Terminal</h3>
                <div id="terminal"></div>
                <div class="terminal-input-group">
                    <input type="text" id="cmd" placeholder="Run shell command (e.g. pip install telebot)" style="margin-bottom:0">
                    <button onclick="sendCommand()" class="btn" style="background:#30363d">Execute</button>
                </div>
            </div>
        {% endif %}
    </div>

    <script>
        var socket = io();
        const terminal = document.getElementById('terminal');

        socket.on('log', function(msg) {
            const line = document.createElement('div');
            line.textContent = "> " + msg;
            terminal.appendChild(line);
            terminal.scrollTop = terminal.scrollHeight;
        });

        function sendCommand() {
            var cmd = document.getElementById('cmd').value;
            if(!cmd) return;
            socket.emit('execute_command', {command: cmd});
            document.getElementById('cmd').value = '';
        }

        function runCode() {
            var code = document.getElementById('code').value;
            var name = document.getElementById('filename').value || 'app.py';
            socket.emit('save_and_run', {code: code, filename: name});
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if request.form.get('password') == PASSWORD:
            session['logged_in'] = True
    return render_template_string(HTML_TEMPLATE, logged_in=session.get('logged_in'))

@socketio.on('execute_command')
def handle_command(data):
    cmd = data['command']
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        socketio.emit('log', line.strip())

@socketio.on('save_and_run')
def handle_run(data):
    filename = data.get('filename', 'app.py')
    filepath = os.path.join(PROJECT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(data.get('code', ''))
    
    socketio.emit('log', f"System: Deploying {filename}...")
    
    def run_script():
        proc = subprocess.Popen(['python', filepath], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            socketio.emit('log', line.strip())

    threading.Thread(target=run_script).start()

if __name__ == '__main__':
    socketio.run(app, host='127.0.0.1', port=8000)
  
