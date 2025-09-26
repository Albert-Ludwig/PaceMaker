import time
import sys

fake_messages = [
    "Encrypting all files... 10%",
    "Encrypting all files... 25%",
    "Encrypting all files... 50%",
    "Encrypting all files... 75%",
    "Encrypting all files... 99%",
    "Error: Cannot stop process...",
    "Just kidding! This is a joke :)"
]

for msg in fake_messages:
    print(msg)
    time.sleep(1.5)

sys.exit(0)
