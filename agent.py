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

def get_next_action(interaction_state, image, main_objective, action_history, last_hover_target):
    """
    Sends the current screen and context to Gemini to get the next action, using a state-based prompt.
    """
    print(f"Thinking about next action... (State: {interaction_state})")
    model = genai.GenerativeModel('gemini-2.5-flash')

    width, height = image.size
    mouse_x, mouse_y = pyautogui.position()
    history_str = "\n".join([f"- {a}" for a in action_history]) if action_history else "No actions taken yet."

    if interaction_state == "AWAITING_CONFIRMATION":
        # Specialized prompt for the "Reflect" step
        hover_context = f"You believe you are hovering over: '{last_hover_target}'." if last_hover_target else ""
        prompt_parts = [
            f"""
            You have just moved your mouse to ({mouse_x}, {mouse_y}). {hover_context}
            Your objective is: '{main_objective}'.

            **Reflect and Decide:**
            1.  Analyze the screenshot and your cursor position.
            2.  Is this the correct place to click to make progress?

            **Next Action:**
            - If YES, the position is correct, your action MUST be: `CLICK "reason for clicking"`
            - If NO, the position is wrong, you MUST EITHER:
                - `MOVE X,Y "new reason"` to a better position.
                - Use a keyboard action like `PRESS "key"` if clicking is not the right approach.

            Do not use `DONE` unless the entire objective is complete.
            Current screen:
            """,
            image,
        ]
    else: # AWAITING_MOVE or any other general state
        # General prompt for deciding the next high-level action
        prompt_parts = [
            f"""
            You are an AI agent. Your goal is to achieve your objective.

            **Objective:** '{main_objective}'

            **Screen & Senses:**
            - The screen is {width}x{height}.
            - The mouse cursor is at ({mouse_x}, {mouse_y}).

            **Self-Correction:**
            Your action history for this objective:
            {history_str}
            If you are stuck, you MUST try a different action. Do not repeat failed actions.

            **Action Format (Strict):**
            - `MOVE X,Y "reason"` (to move the mouse for a future click)
            - `TYPE "text"`
            - `PRESS "key"`
            - `DONE "reason"` (Use this ONLY when the objective is fully complete)

            Determine the single best action to take next.
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
    move_pattern = re.match(r'MOVE\s+(\d+),(\d+)\s+"(.*)"', action, re.IGNORECASE)
    click_pattern = re.match(r'CLICK\s+"(.*)"', action, re.IGNORECASE)
    type_pattern = re.match(r'TYPE\s+"(.*)"', action, re.IGNORECASE)
    press_pattern = re.match(r'PRESS\s+"(.*)"', action, re.IGNORECASE)
    done_pattern = re.match(r'DONE\s+"(.*)"', action, re.IGNORECASE)

    try:
        if move_pattern:
            x, y, reason = int(move_pattern.group(1)), int(move_pattern.group(2)), move_pattern.group(3)
            # Validate coordinates against screen size
            screen_width, screen_height = pyautogui.size()
            if not (0 <= x < screen_width and 0 <= y < screen_height):
                raise ValueError(f"Invalid coordinates ({x}, {y}) outside screen bounds (0-{screen_width-1}, 0-{screen_height-1})")

            # Move to coordinates
            pyautogui.moveTo(x, y, duration=0.1)

        elif click_pattern:
            # Hover for a moment, then click at the current position
            time.sleep(0.2)
            pyautogui.click()

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
            print(f"Completion reason: {done_pattern.group(1)}")
            return True, False
        else:
            print(f"Unknown or malformed command: {action}")
    except Exception as e:
        print(f"Error executing action '{action}': {e}")
        return False, False

    return False, False

# --- Main Loop ---

def run_objective(objective, max_steps=None):
    """Runs the agent for a single objective until it is marked as DONE."""
    print(f"--- Starting Objective: {objective} ---")

    objective_done = False
    attempts = 0
    action_history = []
    last_hover_target = None
    interaction_state = "AWAITING_MOVE"

    while not objective_done:
        if max_steps is not None and attempts >= max_steps:
            print(f"--- Agent Stopped: Max steps ({max_steps}) reached. ---")
            break

        time.sleep(0.5)
        screenshot_image = capture_screen()

        action_command = get_next_action(
            interaction_state, screenshot_image, objective, action_history, last_hover_target
        )

        if action_command:
            action_history.append(action_command)

            # State transition logic
            if interaction_state == "AWAITING_MOVE" and action_command.upper().startswith("MOVE"):
                interaction_state = "AWAITING_CONFIRMATION"
            elif interaction_state == "AWAITING_CONFIRMATION":
                if action_command.upper().startswith("CLICK"):
                    interaction_state = "AWAITING_MOVE" # Reset after click
                # If it's another MOVE, we stay in AWAITING_CONFIRMATION

            # Parse hover context from MOVE commands
            move_match = re.match(r'MOVE\s+(\d+),(\d+)\s+"(.*)"', action_command, re.IGNORECASE)
            if move_match:
                last_hover_target = move_match.group(3)
            elif not action_command.upper().startswith("CLICK"):
                # Reset hover target if the action is not a click or a new move
                last_hover_target = None

            is_objective_done, _ = execute_action(action_command)
            if is_objective_done:
                print(f"--- Objective marked as complete. ---")
                objective_done = True
        else:
            print("Warning: Did not receive a valid command from the model. Retrying...")
            time.sleep(1)

        attempts += 1

    if objective_done:
        print("\n--- Objective Finished Successfully ---")
    else:
        print("\n--- Objective Stopped ---")

def main():
    """The main entry point for the agent."""
    parser = argparse.ArgumentParser(description="AI Desktop Agent")
    parser.add_argument("--objective", type=str, default=None, help="The objective for the agent to perform.")
    parser.add_argument("--max-steps", type=int, default=None, help="Optional max steps per objective (default: unlimited)")
    args = parser.parse_args()

    if args.objective:
        # If an objective is provided via command line, run it
        run_objective(args.objective, args.max_steps)
    else:
        # Otherwise, enter interactive mode
        print("No objective provided. Starting in interactive mode.")
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
