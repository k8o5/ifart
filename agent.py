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

def create_plan(objective):
    """
    Generates a step-by-step plan to achieve the given objective.
    """
    print("Asking Gemini to create a plan...")
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    You are an AI planner. Your task is to create a step-by-step plan to achieve the following objective.
    The plan should be a sequence of simple, high-level actions.
    For any web searches, you must use DuckDuckGo.

    Objective: '{objective}'

    Provide the plan as a numbered list. For example:
    1. Open Firefox.
    2. Navigate to duckduckgo.com.
    3. Search for "best open source projects".
    4. ...

    Now, create the plan for the objective above.
    """

    try:
        response = model.generate_content(prompt)
        plan_text = response.text.strip()
        # Parse the numbered list into a Python list
        plan_steps = [step.strip() for step in re.findall(r'^\d+\.\s+(.*)', plan_text, re.MULTILINE)]
        if not plan_steps:
            # Fallback if the model doesn't return a numbered list
            plan_steps = [line.strip() for line in plan_text.split('\n') if line.strip()]

        print("--- Plan Created ---")
        for i, step in enumerate(plan_steps, 1):
            print(f"{i}. {step}")
        print("--------------------")

        return plan_steps
    except Exception as e:
        print(f"Error creating plan with Gemini: {e}")
        return []

def get_next_action(image, main_objective, plan, current_step):
    """
    Sends the current screen and context to the Gemini model to get the next action.
    """
    print(f"Thinking about next action for step: {current_step}")
    model = genai.GenerativeModel('gemini-2.5-flash')

    width, height = image.size
    plan_str = "\n".join([f"{i+1}. {s}" for i, s in enumerate(plan)])

    prompt_parts = [
        f"""
        You are an AI agent controlling a desktop.
        Your main objective is: '{main_objective}'.

        You have created the following plan:
        {plan_str}

        You are currently on this step: '{current_step}'.

        Analyze the screenshot and decide the single next action to take.

        **Action Strategy:**
        1.  **Prioritize Keyboard:** Always prefer keyboard actions (`PRESS`, `TYPE`).
        2.  **Mouse for Necessity:** Use mouse actions (`CLICK`) only when a keyboard action is not possible.
        3.  **Be Precise:** For mouse clicks, provide the exact X,Y coordinates. The screen is {width}x{height}.
        4.  **Sequences:** Use `COMMANDS` to group a short sequence of actions.
        5.  **Step Completion:** If you have successfully completed the current step, your action MUST be `DONE "reason for completion"`. This will move you to the next step.

        **Action Format (Strict):**
        - `TYPE "text to type"`
        - `PRESS "key"` (e.g., "enter", "tab", "ctrl+f")
        - `CLICK X,Y "reason"`
        - `COMMANDS ["action1", "action2"]`
        - `DONE "reason"`

        Now, determine the most efficient action to progress on your current step.
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
    """Runs the agent for a single objective using a plan-based approach."""
    print(f"--- Starting Objective: {objective} ---")

    plan = create_plan(objective)
    if not plan:
        print("--- Agent Stopped: Could not create a plan. ---")
        return

    # Main loop iterates through the plan
    for i, step in enumerate(plan):
        print(f"\n--- Executing Step {i+1}/{len(plan)}: {step} ---")

        step_done = False
        attempts = 0
        max_attempts_per_step = 10  # Failsafe to prevent infinite loops

        # Sub-loop for each step
        while not step_done:
            if attempts >= max_attempts_per_step:
                print(f"--- Warning: Max attempts reached for step. Moving to next one. ---")
                break

            if max_steps is not None and i >= max_steps:
                print(f"--- Agent Stopped: Global max steps ({max_steps}) reached. ---")
                return

            time.sleep(0.5)
            screenshot_image = capture_screen()

            # Get next action based on the full context
            action_command = get_next_action(screenshot_image, objective, plan, step)

            if action_command:
                # The 'DONE' command now signals step completion
                is_step_done, _ = execute_action(action_command)
                if is_step_done:
                    print(f"--- Step {i+1} marked as complete. ---")
                    step_done = True  # Exit the sub-loop to the next step
            else:
                print("Warning: Did not receive a valid command from the model. Retrying...")
                time.sleep(1) # Wait a bit longer on API failure

            attempts += 1

    print("\n--- Objective Finished ---")

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
