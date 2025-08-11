import pyautogui
import google.generativeai as genai
import os
import time
import re
import argparse
from PIL import Image
import random
import json

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

    # Enhanced prompt for keyboard-first interaction
    prompt_parts = [
        f"""
        You are an AI agent controlling a desktop. Your primary mode of interaction is the KEYBOARD.
        Your objective is: '{objective}'.
        Analyze the screenshot and decide the next action or sequence of actions to take.

        **Action Strategy:**
        1.  **Prioritize Keyboard:** Always prefer keyboard actions (`PRESS`, `TYPE`). Use keyboard shortcuts, navigation (Tab, arrows), and commands. This is faster and more reliable.
        2.  **Use Mouse for Complex Interactions:** Use mouse actions (`CLICK`, `DRAG`) only when necessary. Your mouse movements are human-like, with natural-seeming acceleration and slight imprecision. This is useful for CAPTCHAs.
        3.  **Be Precise:** When you must use the mouse, calculate the exact center coordinates (X,Y) of the target element. The screen dimensions are {width}x{height}.
        4.  **Sequence Commands:** For multi-step tasks, use the `COMMANDS` action to group a sequence of actions together.

        **Action Format:**
        - `TYPE "text to type"`
        - `PRESS "key_name"` (e.g., "enter", "tab", "ctrl+c")
        - `CLICK X,Y "reason"`
        - `DRAG X1,Y1 TO X2,Y2 "reason"`
        - `COMMANDS ["action1", "action2", ...]` (for a sequence of actions)
        - `DONE "reason"` (when the objective is complete)

        **Example Keyboard-First Thinking:**
        - To open a file menu, instead of `CLICK 12,34 "File Menu"`, prefer `PRESS "alt+f"`.
        - To open a terminal, type a command, and press enter: `COMMANDS ["PRESS 'win'", "TYPE 'terminal'", "PRESS 'enter'", "TYPE 'echo hello'", "PRESS 'enter'"]`

        Now, analyze the screen and determine the most efficient action(s).
        Current screen:
        """,
        image,
    ]

    try:
        response = model.generate_content(prompt_parts)
        action_text = response.text.strip()
        return action_text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def get_vision_understanding(image):
    """
    Uses Gemini to describe the given image.
    """
    print("Gemini is trying to understand the screen...")
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt_parts = [
        "Describe what you see on the screen. Be concise and focus on the most important elements.",
        image,
    ]
    try:
        response = model.generate_content(prompt_parts)
        return response.text.strip()
    except Exception as e:
        print(f"Error calling Gemini API for vision understanding: {e}")
        return "Error: Could not understand the screen."

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
    drag_pattern = re.match(r'DRAG\s+(\d+),(\d+)\s+TO\s+(\d+),(\d+)\s+"(.*)"', action, re.IGNORECASE)
    commands_pattern = re.match(r'COMMANDS\s+(.*)', action, re.IGNORECASE)

    try:
        if commands_pattern:
            commands_list_str = commands_pattern.group(1)
            try:
                commands_list = json.loads(commands_list_str)
                if isinstance(commands_list, list):
                    for command in commands_list:
                        # Recursive call to execute each command in the list
                        execute_action(command)
                    return False, True  # Not done, but it was a COMMANDS action
                else:
                    raise ValueError("COMMANDS action requires a list of strings.")
            except json.JSONDecodeError:
                print(f"Error: Could not decode JSON in COMMANDS: {commands_list_str}")
            except ValueError as e:
                print(f"Error: {e}")
            return False, False # Error case

        elif click_pattern:
            x, y, reason = int(click_pattern.group(1)), int(click_pattern.group(2)), click_pattern.group(3)
            # Validate coordinates against screen size
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x < screen_width and 0 <= y < screen_height):
                raise ValueError(f"Invalid coordinates ({x}, {y}) outside screen bounds (0-{screen_width-1}, 0-{screen_height-1})")

            # Human-like mouse movement
            target_x = x + random.randint(-2, 2)
            target_y = y + random.randint(-2, 2)

            # Ensure target is still within bounds
            target_x = max(0, min(screen_width - 1, target_x))
            target_y = max(0, min(screen_height - 1, target_y))

            duration = random.uniform(0.2, 0.7)
            tween = pyautogui.easeInOutQuad
            pyautogui.moveTo(target_x, target_y, duration=duration, tween=tween)
            pyautogui.click()

        elif drag_pattern:
            x1, y1, x2, y2, reason = (int(drag_pattern.group(1)), int(drag_pattern.group(2)),
                                      int(drag_pattern.group(3)), int(drag_pattern.group(4)),
                                      drag_pattern.group(5))

            screen_width, screen_height = pyautogui.size()
            if not (0 <= x1 < screen_width and 0 <= y1 < screen_height and
                    0 <= x2 < screen_width and 0 <= y2 < screen_height):
                raise ValueError(f"Invalid coordinates in DRAG command.")

            # Human-like drag
            pyautogui.moveTo(x1, y1, duration=random.uniform(0.2, 0.5), tween=pyautogui.easeInOutQuad)
            pyautogui.mouseDown()
            pyautogui.moveTo(x2, y2, duration=random.uniform(0.5, 1.0), tween=pyautogui.easeInOutQuad)
            pyautogui.mouseUp()

        elif type_pattern:
            text_to_type = type_pattern.group(1)
            pyautogui.write(text_to_type, interval=0.05)
        elif press_pattern:
            key_string = press_pattern.group(1).lower()
            if '+' in key_string:
                keys = [k.strip() for k in key_string.split('+')]
                pyautogui.hotkey(*keys)
            else:
                pyautogui.press(key_string)
        elif done_pattern:
            print(f"Objective achieved: {done_pattern.group(1)}")
            return True, False
        else:
            print(f"Unknown or malformed command: {action}")
    except Exception as e:
        print(f"Error executing action '{action}': {e}")
        return False, False

    return False, False

# --- Main Loop ---

def run_objective(objective, max_steps=None):
    """Runs the agent for a single objective."""
    print(f"--- Starting Objective ---")
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
            is_done, is_commands = execute_action(action_command)
            if is_commands:
                # After a COMMANDS sequence, get a vision understanding of the screen
                time.sleep(1.0) # Wait a moment for the UI to settle
                screenshot_image = capture_screen()
                vision_description = get_vision_understanding(screenshot_image)
                print(f"\n--- Screen Description ---\n{vision_description}\n--------------------------\n")

        else:
            print("Did not receive a command. Retrying...")
            sleep_duration += 0.5  # Exponential backoff for retries

        step_count += 1

    if is_done:
        print("--- Objective Finished Successfully ---")
    else:
        print("--- Objective Stopped ---")

def main():
    """The main interactive loop for the agent."""
    parser = argparse.ArgumentParser(description="AI Desktop Agent")
    parser.add_argument("--max-steps", type=int, default=None, help="Optional max steps per objective (default: unlimited)")
    args = parser.parse_args()

    while True:
        objective = input("Please enter your next objective (or type 'exit' to quit): ")
        if objective.lower() == 'exit':
            print("Exiting agent.")
            break
        if not objective.strip():
            print("Objective cannot be empty.")
            continue

        run_objective(objective, args.max_steps)
        print("\n" + "="*30)
        print("Objective complete. Ready for the next one.")
        print("="*30 + "\n")


if __name__ == "__main__":
    main()
