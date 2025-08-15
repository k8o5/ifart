# Basis-Image Debian 11 (Bullseye) - restored to original base for compatibility
FROM debian:11-slim

# Metadaten für das Image
LABEL maintainer="Docker GUI"
LABEL version="2.2"
LABEL description="Debian mit XFCE, VNC-Server und einem AI-Agenten (Gemini oder Gemma)"

# Build-Argument zur Auswahl des Modellanbieters (gemini oder gemma)
ARG MODEL_PROVIDER=gemini

# Umgebungsvariablen für die VNC-Einrichtung und Agent
ENV DISPLAY=:1 \
    VNC_PORT=5901 \
    NO_VNC_PORT=6901 \
    VNC_RESOLUTION=1280x720 \
    VNC_PASSWORD=password \
    AGENT_OBJECTIVE="Open the file manager and create a new folder named 'Test-Folder'." \
    AGENT_MODEL=${MODEL_PROVIDER} \
    GOOGLE_API_KEY=""

# Installation der notwendigen Pakete
# Inklusive curl für den Ollama-Installer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    dbus-x11 \
    net-tools \
    novnc \
    procps \
    tigervnc-standalone-server \
    wget \
    xfce4 \
    xfce4-goodies \
    python3 \
    python3-pip \
    scrot \
    python3-tk \
    python3-dev \
    gnome-screenshot \
    xfce4-terminal \
    firefox-esr \
    curl \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Conditionally install Ollama if MODEL_PROVIDER is 'gemma'
# Note: This runs the install script. The service itself is started in vnc_startup.sh
RUN if [ "$MODEL_PROVIDER" = "gemma" ]; then \
        echo "Installing Ollama for Gemma model..."; \
        curl -f https://ollama.com/install.sh | sh; \
    else \
        echo "Skipping Ollama installation for Gemini model."; \
    fi

# Install Python libraries for the agent
RUN pip3 install --no-cache-dir \
    pyautogui \
    google-generativeai \
    Pillow \
    requests

# Copy the agent script into the image
COPY agent.py /agent.py

# Erstellen des VNC-Startskripts
# This script now handles the conditional startup of the Ollama service and the agent itself
RUN mkdir -p /opt/startup/
COPY <<EOF /opt/startup/vnc_startup.sh
#!/bin/bash
export USER=root

# --- VNC Setup ---
mkdir -p /root/.vnc
echo "\$VNC_PASSWORD" | vncpasswd -f > /root/.vnc/passwd
chmod 600 /root/.vnc/passwd

# --- Start Desktop and VNC ---
startxfce4 &
sleep 2
vncserver "\$DISPLAY" -depth 24 -geometry "\$VNC_RESOLUTION" -localhost no &
/usr/share/novnc/utils/launch.sh --vnc localhost:"\$VNC_PORT" --listen "\$NO_VNC_PORT" &

# --- Agent Startup Logic ---
# Wait for the desktop environment to be ready
sleep 5

# Launch the agent in a terminal window
# The logic inside the terminal will handle which model to run
xfce4-terminal -e "/bin/bash -c '
    if [ \"\$AGENT_MODEL\" = \"gemma\" ]; then
        echo \"--- Gemma Model Setup --- \"
        echo \"Starting Ollama service...\"
        /usr/local/bin/ollama serve &

        echo \"Waiting for Ollama to be ready...\"
        while ! curl -s --head http://localhost:11434 > /dev/null; do
            sleep 1
        done
        echo \"Ollama is ready.\"

        echo \"Pulling model ai/gemma3:latest. This may take a while...\"
        /usr/local/bin/ollama pull ai/gemma3:latest
        echo \"Model pull complete.\"

    else
        echo \"--- Gemini Model Setup --- \"
        if [ -z \"\$GOOGLE_API_KEY\" ]; then
            echo \"ERROR: GOOGLE_API_KEY is not set. The agent will fail.\"
            echo \"Please provide it with --build-arg GOOGLE_API_KEY=\\\"YOUR_KEY\\\"\"
        fi
    fi

    echo \"Starting agent...\"
    python3 /agent.py --objective \"\$AGENT_OBJECTIVE\"

    # Keep the terminal open for debugging after the script finishes
    echo \"Agent script finished. Press Enter to close this terminal.\"
    read
'"
EOF
RUN chmod +x /opt/startup/vnc_startup.sh

# Ports freigeben
EXPOSE 5901 6901

# Startbefehl
CMD ["/opt/startup/vnc_startup.sh"]
