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
    Pillow

# Copy the agent script into the image
COPY agent.py /agent.py

# --- AUTOSTART CONFIGURATION ---
# Create the autostart directory and the .desktop file to run the agent on startup with optional objective
RUN mkdir -p /root/.config/autostart
COPY <<EOF /root/.config/autostart/agent.desktop
[Desktop Entry]
Type=Application
Name=AI Agent (Gemini 2.5 Flash)
Exec=xfce4-terminal -e "python3 /agent.py --objective '$AGENT_OBJECTIVE'"
StartupNotify=false
Terminal=false
EOF

# Erstellen des VNC-Startskripts (restored to original with enhancements for robust startup)
RUN mkdir -p /opt/startup/
COPY <<EOF /opt/startup/vnc_startup.sh
#!/bin/bash
export USER=root
mkdir -p /root/.vnc
echo "$VNC_PASSWORD" | vncpasswd -f > /root/.vnc/passwd
chmod 600 /root/.vnc/passwd
# Start XFCE session to ensure autostart works (added for reliability)
startxfce4 &
# Wait briefly for desktop to initialize
sleep 2
# Start VNC server (as in original)
vncserver "$DISPLAY" -depth 24 -geometry "$VNC_RESOLUTION" -localhost no
# Start noVNC (as in original)
/usr/share/novnc/utils/launch.sh --vnc localhost:"$VNC_PORT" --listen "$NO_VNC_PORT"
EOF
RUN chmod +x /opt/startup/vnc_startup.sh

# Ports freigeben
EXPOSE 5901 6901

# Startbefehl
CMD ["/opt/startup/vnc_startup.sh"]
