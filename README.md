# AI Desktop Agent

This project contains a simple AI agent that can use either a powerful cloud-based model (Google's Gemini) or a local, private model (`ai/gemma3:latest`) to interact with a desktop environment. The agent can be given an objective, and it will use keyboard and mouse actions to try and achieve it.

The agent is designed to run inside a Docker container that provides a full Debian XFCE desktop environment accessible via VNC.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your machine.
- **For Gemini Model**: A Google API Key with the Gemini API enabled. You can get one from [Google AI Studio](https://aistudio.google.com/app/apikey).
- **For Gemma Model**: No API key is required. The model runs locally within the Docker container.

## How to Run

### 1. Choose your AI Model

You can select which model to use when you build the Docker image by setting the `MODEL_PROVIDER` build argument.

- `gemini` (Default): Uses the Google Gemini 2.5 Flash model via the API. Requires a `GOOGLE_API_KEY`.
- `gemma`: Uses the `ai/gemma3:latest` model, which will be downloaded and run locally by Ollama inside the container. This is slower but works offline and requires no API key.

### 2. Build the Docker Image

Open your terminal in the project root directory and run the command corresponding to your chosen model.

**Option A: Build with Gemini (Default)**

You must provide your Google API key at build time.

```bash
docker build \
  --build-arg GOOGLE_API_KEY="YOUR_API_KEY_HERE" \
  -t ai-desktop-agent:gemini .
```

**Option B: Build with Gemma (Local Model)**

This will download the Gemma model (~5.5 GB) during the build process, so the first build will take some time.

```bash
docker build \
  --build-arg MODEL_PROVIDER=gemma \
  -t ai-desktop-agent:gemma .
```

### 3. Run the Docker Container

After the image is built, you can run it as a container. This command will start the container in detached mode and map the VNC ports to your local machine.

```bash
# Make sure to use the correct image tag (e.g., :gemini or :gemma)
docker run -d -p 5901:5901 -p 6901:6901 --name my-agent ai-desktop-agent:gemini
```
- The VNC server is on port `5901`.
- A web-based noVNC client is on port `6901`.

### 4. Connect to the Desktop

You can connect to the agent's desktop environment using any VNC client or by using the web client.

- **VNC Client**: Connect to `localhost:5901`. The password is `password`.
- **Web Client**: Open your web browser and navigate to `http://localhost:6901`. Click "Connect" and enter the password `password`.

### 5. Watch the Agent

Upon connecting, you will see an XFCE desktop. An XFCE terminal will open automatically and start the `agent.py` script. The agent will then begin working on its default objective, using the model you selected during the build.

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
