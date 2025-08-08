import pyautogui
import google.generativeai as genai
import os
import time
import re
import argparse
from PIL import Image

# --- Configuration ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Please set the GOOGLE_API_KEY environment variable.")

genai.configure(api_key=api_key)

# --- Core Functions ---

def capture_screen():
    """Captures a screenshot in memory and returns it as a PIL Image object."""
    screenshot = pyautogui.screenshot()
    return screenshot

def get_next_action(image, objective):
    """
    Sends the current screen and objective to the Gemini model to get the next action.
    Uses the user-specified model for compatibility.
    """
    print("Thinking with Gemini 2.5 Flash...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Get image dimensions for precise coordinate calculation
    width, height = image.size
    
    # Enhanced prompt for 100% precise coordinate detection
    prompt_parts = [
        f"""
        You are an AI agent controlling a desktop (primarily Debian XFCE, but adapt to visible UI elements if it looks like Windows or another OS).
        Analyze the screenshot carefully to identify exact pixel coordinates for interactions.
        Screenshot dimensions: {width}x{height} pixels.
        Steps to follow for precision:
        1. Examine the entire image for UI elements like icons, buttons, menus, or text relevant to the objective.
        2. Identify the target element's position: note its shape, color, text, and bounding box.
        3. Calculate the exact center coordinates (X,Y) of the interactive area—aim for the middle to ensure accurate clicks.
        4. Double-check: Ensure X is between 0 and {width-1}, Y between 0 and {height-1}. Avoid guessing; base on visible pixels.
        Decide the SINGLE next action to achieve: '{objective}'.
        Respond with ONE line ONLY, using:
        - CLICK X,Y "reason" (e.g., CLICK 75,32 "Click menu icon center")
        - TYPE "text" (e.g., TYPE "hello")
        - PRESS "key" (e.g., PRESS "enter")
        - DONE "reason" (when complete)
        Be 100% precise with coordinates based on the image.
        Current screen:
        """,
        image,
    ]

    try:
        response = model.generate_content(prompt_parts)
        # Extract the first line of text for safety
        action_text = response.text.strip().split('\n')[0]
        return action_text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def execute_action(action):
    """Parses and executes the action string from the LLM using regex for robustness, with coordinate validation."""
    if not action:
        print("Received an empty action. Skipping.")
        return False
    
    print(f"Executing: {action.strip()}")
    action = action.strip()
    
    # Regex patterns for reliable parsing
    click_pattern = re.match(r'CLICK\s+(\d+),(\d+)\s+"(.*)"', action, re.IGNORECASE)
    type_pattern = re.match(r'TYPE\s+"(.*)"', action, re.IGNORECASE)
    press_pattern = re.match(r'PRESS\s+"(.*)"', action, re.IGNORECASE)
    done_pattern = re.match(r'DONE\s+"(.*)"', action, re.IGNORECASE)
    
    try:
        if click_pattern:
            x, y, reason = int(click_pattern.group(1)), int(click_pattern.group(2)), click_pattern.group(3)
            # Validate coordinates against screen size
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x < screen_width and 0 <= y < screen_height):
                raise ValueError(f"Invalid coordinates ({x}, {y}) outside screen bounds (0-{screen_width-1}, 0-{screen_height-1})")
            pyautogui.click(x, y)
        elif type_pattern:
            text_to_type = type_pattern.group(1)
            pyautogui.write(text_to_type, interval=0.05)  # Faster typing interval
        elif press_pattern:
            key = press_pattern.group(1).lower()
            pyautogui.press(key)
        elif done_pattern:
            print(f"Objective achieved: {done_pattern.group(1)}")
            return True
        else:
            print(f"Unknown or malformed command: {action}")
    except Exception as e:
        print(f"Error executing action '{action}': {e}")
        return False  # Return False to continue looping
    
    return False

# --- Main Loop ---

def main(objective, max_steps=None):
    """The main function to run the agent."""
    print(f"--- Starting Agent ---")
    print(f"Objective: {objective}")

    is_done = False
    step_count = 0
    sleep_duration = 0.5  # Reduced for speed; adjust as needed
    
    while not is_done:
        if max_steps is not None and step_count >= max_steps:
            print(f"--- Agent Stopped: Max steps ({max_steps}) reached ---")
            break
        
        time.sleep(sleep_duration)  # Minimal delay for UI updates
        
        screenshot_image = capture_screen()
        action_command = get_next_action(screenshot_image, objective)
        
        if action_command:
            is_done = execute_action(action_command)
        else:
            print("Did not receive a command. Retrying...")
            sleep_duration += 0.5  # Exponential backoff for retries
        
        step_count += 1
            
    if is_done:
        print("--- Agent Finished Successfully ---")
    else:
        print("--- Agent Stopped ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Desktop Agent")
    parser.add_argument("--objective", default="Open the file manager and create a new folder named 'Gemini-2.5-Test'.", help="Set the agent's objective")
    parser.add_argument("--max-steps", type=int, default=None, help="Optional max steps to prevent infinite loops (default: unlimited)")
    args = parser.parse_args()
    main(args.objective, args.max_steps)
