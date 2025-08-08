import pyautogui
import google.generativeai as genai
import os
import time
from PIL import Image

# --- Configuration ---
# Get your Google API key from Google AI Studio
# It's recommended to use an environment variable for security
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Please set the GOOGLE_API_KEY environment variable.")

genai.configure(api_key=api_key)

# --- Core Functions ---

def capture_screen():
    """Takes a screenshot and returns it as a PIL Image object."""
    filepath = "screenshot.png"
    pyautogui.screenshot(filepath)
    return Image.open(filepath)

def get_next_action(image, objective):
    """
    Sends the current screen and objective to the Gemini model to get the next action.
    """
    print("Thinking with Gemini...")
    # Using gemini-1.5-pro for its advanced multimodal reasoning
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    # System prompt to guide the model's behavior
    prompt_parts = [
        """
        You are an AI agent controlling a Debian XFCE desktop.
        You see a screenshot of the desktop.
        Your task is to decide the single next action to perform to achieve the user's objective.
        Respond with a single command in a single line. Available commands are:
        - CLICK X,Y "reasoning for the click" (e.g., CLICK 75,32 "Click the Applications menu")
        - TYPE "text to type" (e.g., TYPE "hello world from Gemini")
        - PRESS "key" (e.g., PRESS "enter" or "esc")
        - DONE "reasoning" (when the objective is complete)
        Be precise. Analyze the image carefully to determine the exact coordinates for clicks.
        The user's objective is: '""",
        objective,
        "'.\n\nHere is the current screen:",
        image,
    ]

    try:
        response = model.generate_content(prompt_parts)
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def execute_action(action):
    """Parses and executes the action string from the LLM."""
    if not action:
        print("Received an empty action. Skipping.")
        return False
        
    print(f"Executing: {action.strip()}")
    # Sanitize the action string
    action = action.strip()
    parts = action.split(" ", 1)
    command = parts[0].upper()

    try:
        if command == "CLICK":
            coords_part, reason = parts[1].split(" ", 1)
            x_str, y_str = coords_part.split(',')
            x, y = int(x_str), int(y_str)
            pyautogui.click(x, y)
        elif command == "TYPE":
            text_to_type = parts[1].strip('"')
            pyautogui.write(text_to_type, interval=0.1)
        elif command == "PRESS":
            key = parts[1].strip('"')
            pyautogui.press(key)
        elif command == "DONE":
            print("Objective achieved!")
            return True
        else:
            print(f"Unknown command: {action}")
    except Exception as e:
        print(f"Error executing action '{action}': {e}")
    
    return False

# --- Main Loop ---

def main():
    """The main function to run the agent."""
    objective = input("Please state your objective for the Gemini agent: ")
    is_done = False

    while not is_done:
        time.sleep(2)  # Give the UI time to update after an action
        
        screenshot_image = capture_screen()
        action_command = get_next_action(screenshot_image, objective)
        
        if action_command:
            is_done = execute_action(action_command)
        else:
            print("Did not receive a command. Retrying...")

if __name__ == "__main__":
    main()
