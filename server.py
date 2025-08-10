import os
import subprocess
from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__, template_folder='templates', static_folder='static')

# --- Routes ---

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serves static files (CSS, JS)."""
    return send_from_directory('static', filename)

@app.route('/agent', methods=['POST'])
def run_agent():
    """
    Receives a task and launches a new agent process in the background.
    """
    data = request.get_json()
    if not data or 'task' not in data:
        return jsonify({"status": "error", "message": "Task not provided"}), 400

    task = data['task']
    google_api_key = os.environ.get("GOOGLE_API_KEY")

    if not google_api_key:
        print("WARNING: GOOGLE_API_KEY is not set. Agent will fail.")
        # Optionally, you could prevent the agent from starting
        # return jsonify({"status": "error", "message": "Server is missing GOOGLE_API_KEY"}), 500

    print(f"Received task: '{task}'. Launching agent...")

    try:
        # Command to execute the agent script
        # The script is in /app, and the server's working dir is /app
        command = ["python3", "/app/agent.py", "--objective", task]

        # Use Popen for non-blocking execution
        # Pass the environment variables, including the API key
        subprocess.Popen(command, env=os.environ)

        print(f"Agent for task '{task}' launched successfully.")
        return jsonify({"status": "success", "message": f"Agent for task '{task}' launched."})

    except Exception as e:
        print(f"Error launching agent: {e}")
        return jsonify({"status": "error", "message": f"Failed to launch agent: {e}"}), 500

if __name__ == '__main__':
    # Using port 8080 as 5000 can sometimes be used by other services.
    # Host '0.0.0.0' makes it accessible from outside the container.
    app.run(host='0.0.0.0', port=8080, debug=True)
