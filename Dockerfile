# Basis-Image Debian 11 (Bullseye)
FROM debian:11

# Metadaten für das Image
LABEL maintainer="Docker GUI"
LABEL version="1.0"
LABEL description="Debian mit XFCE und VNC-Server"

# Umgebungsvariablen für die VNC-Einrichtung
ENV DISPLAY=:1 \
    VNC_PORT=5901 \
    NO_VNC_PORT=6901 \
    VNC_RESOLUTION=1280x720 \
    VNC_PASSWORD=password

# Installation der notwendigen Pakete
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    dbus-x11 \
    net-tools \
    novnc \
    procps \
    tigervnc-standalone-server \
    wget \
    xfce4 \
    xfce4-goodies && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Erstellen des VNC-Startskripts
RUN mkdir -p /opt/startup/
COPY <<EOF /opt/startup/vnc_startup.sh
#!/bin/bash
export USER=root
mkdir -p /root/.vnc
echo "\$VNC_PASSWORD" | vncpasswd -f > /root/.vnc/passwd
chmod 600 /root/.vnc/passwd
vncserver "\$DISPLAY" -depth 24 -geometry "\$VNC_RESOLUTION" -localhost no
/usr/share/novnc/utils/launch.sh --vnc localhost:"\$VNC_PORT" --listen "\$NO_VNC_PORT"
EOF
RUN chmod +x /opt/startup/vnc_startup.sh

# Ports freigeben
EXPOSE 5901 6901

# Startbefehl
CMD ["/opt/startup/vnc_startup.sh"]
