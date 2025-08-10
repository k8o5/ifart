# Basis-Image Debian 11 (Bullseye) - restored to original base for compatibility
FROM debian:11-slim

# Metadaten für das Image
LABEL maintainer="Docker GUI"
LABEL version="2.1"
LABEL description="Debian mit XFCE, VNC-Server und Google Gemini 2.5 Flash Agent (Autostart, Optimized for Speed and Precision)"

# Umgebungsvariablen für die VNC-Einrichtung und Agent
ENV DISPLAY=:1 \
    VNC_PORT=5901 \
    NO_VNC_PORT=6901 \
    VNC_RESOLUTION=1280x720 \
    VNC_PASSWORD=password \
    AGENT_OBJECTIVE="Open the file manager and create a new folder named 'Gemini-2.5-Test'." \
    GOOGLE_API_KEY=""

# Installation der notwendigen Pakete (restored ALL original packages for full compatibility)
# Includes net-tools, procps, wget, and essentials for pyautogui (X11, screenshot tools) and XFCE/VNC
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
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Python libraries for the agent (no-cache for smaller image)
RUN pip3 install --no-cache-dir \
    pyautogui \
    google-generativeai \
    Pillow \
    flask

# Copy the entire application into /app
WORKDIR /app
COPY server.py agent.py ./
COPY static/ ./static/
COPY templates/ ./templates/
WORKDIR /

# Erstellen des VNC-Startskripts
RUN mkdir -p /opt/startup/
COPY <<EOF /opt/startup/vnc_startup.sh
#!/bin/bash
export USER=root
mkdir -p /root/.vnc
echo "$VNC_PASSWORD" | vncpasswd -f > /root/.vnc/passwd
chmod 600 /root/.vnc/passwd
# Start XFCE session
startxfce4 &
# Wait briefly for desktop to initialize
sleep 2
# Change to the app directory before running the server
cd /app
# Start the Flask web server in the background
python3 server.py &
# Launch Firefox to the web UI
firefox-esr http://localhost:8080 &
# Start VNC server
vncserver "$DISPLAY" -depth 24 -geometry "$VNC_RESOLUTION" -localhost no
# Start noVNC
/usr/share/novnc/utils/launch.sh --vnc localhost:"$VNC_PORT" --listen "$NO_VNC_PORT"
EOF
RUN chmod +x /opt/startup/vnc_startup.sh

# Ports freigeben
EXPOSE 5901 6901 8080

# Startbefehl
CMD ["/opt/startup/vnc_startup.sh"]
