# AI Desktop Agent

This project contains a simple AI agent that uses Google's Gemini 2.5 Flash model to interact with a desktop environment. The agent can be given an objective, and it will use keyboard and mouse actions to try and achieve it.

The agent is designed to run inside a Docker container that provides a full Debian XFCE desktop environment accessible via VNC.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your machine.
- A Google API Key with the Gemini API enabled. You can get one from [Google AI Studio](https://aistudio.google.com/app/apikey).

## How to Run

1.  **Set your Google API Key:**
    The agent requires your Google API key to function. You must set it in the `Dockerfile` before building the image.

    Open the `Dockerfile` and replace the placeholder value for `GOOGLE_API_KEY` with your actual key:

    ```Dockerfile
    # ...
    ENV DISPLAY=:1 \
        # ...
        GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

2.  **Build the Docker Image:**
    Open your terminal in the project root directory and run the following command to build the image.

    ```bash
    docker build -t ai-desktop-agent .
    ```

3.  **Run the Docker Container:**
    After the image is built, you can run it as a container. This command will start the container in detached mode and map the VNC ports to your local machine.

    ```bash
    docker run -d -p 5901:5901 -p 6901:6901 --name my-agent ai-desktop-agent
    ```
    - The VNC server is on port `5901`.
    - A web-based noVNC client is on port `6901`.

4.  **Connect to the Desktop:**
    You can connect to the agent's desktop environment using any VNC client or by using the web client.

    - **VNC Client**: Connect to `localhost:5901`. The password is `password`.
    - **Web Client**: Open your web browser and navigate to `http://localhost:6901`. Click "Connect" and enter the password `password`.

5.  **Watch the Agent:**
    Upon connecting, you will see an XFCE desktop. An XFCE terminal will open automatically and start the `agent.py` script. The agent will then begin working on its default objective.

## Configuration

### Changing the Objective

You can change the agent's objective by setting the `AGENT_OBJECTIVE` environment variable in the `Dockerfile` before building, or by overriding it when you run the container.

**Option 1: Set in Dockerfile**
```Dockerfile
#...
ENV AGENT_OBJECTIVE="Open firefox and search for the weather."
#...
```

**Option 2: Override with `docker run`**
```bash
docker run -d -p 5901:5901 -p 6901:6901 \
  -e AGENT_OBJECTIVE="Open firefox and search for the weather." \
  --name my-agent ai-desktop-agent
```

### Manual Control

If you want to run the agent manually or debug, you can get a shell inside the running container:
```bash
docker exec -it my-agent /bin/bash
```

From there, you can run the agent script with a custom objective:
```bash
python3 /agent.py --objective "Your custom objective here."
```

## Troubleshooting

### Docker Build Error on Arch Linux

If you encounter an error message similar to `failed to add the host ... operation not supported` while running `docker build`, it is likely due to a Docker networking issue on your host system.

To resolve this, you can use the host's network for the build process by adding the `--network=host` flag to the build command:

```bash
docker build --network=host -t ai-desktop-agent .
```
