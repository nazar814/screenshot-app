import win32clipboard
import time

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
        
monitor_clipboard()