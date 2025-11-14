# This file is used to do the user authentication, including registration and login.
import json, hashlib, os

USER_FILE = "data/users.json"
DEVICE_FILE = "data/Pacemaker_device_name.json" # File to store known device port/name mappings

def load_users():
    if not os.path.exists(USER_FILE):
        raise FileNotFoundError(f"{USER_FILE} is not created")
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha512(password.encode()).hexdigest()

def register_user(name, password):
    users = load_users()
    if len(users) >= 10:
        return "Max users reached"
    if any(u["name"] == name for u in users):
        return "User already exists"
    users.append({"name": name, "password": hash_password(password)})
    save_users(users)
    return "Registration successful"

def login_user(name, password):
    users = load_users()
    hashed = hash_password(password)
    for u in users:
        if u["name"] == name and u["password"] == hashed:
            return "Login successful"
    return "Invalid credentials"

def logout_account(username, user_data_file):
    import json, os

    if not os.path.exists(user_data_file):
        return False
    
    try:
        with open(user_data_file, "r") as f:
            users = json.load(f)
        
        original_count = len(users)
        users = [u for u in users if u.get("name") != username]
        
        if len(users) < original_count:  
            with open(user_data_file, "w") as f:
                json.dump(users, f, indent=2)
            return True
        else:
            return False  
    except Exception:
        return False

# Device name management functions
def load_device_names():
    """
    Loads the list of known devices from the JSON file.
    Creates the file/directory if it doesn't exist.
    """
    os.makedirs("data", exist_ok=True) # Ensure the 'data' directory exists
    if not os.path.exists(DEVICE_FILE):
        with open(DEVICE_FILE, "w") as f:
            json.dump([], f) # Create an empty list if file is new
        return []
    try:
        with open(DEVICE_FILE, "r") as f:
            return json.load(f) # Load the existing list
    except json.JSONDecodeError:
        return [] # Return empty list if JSON is corrupt

def save_device_names(devices):
    """Saves the updated list of devices back to the JSON file."""
    with open(DEVICE_FILE, "w") as f:
        json.dump(devices, f, indent=2)

def get_or_assign_device_name(port_name: str) -> str:
    """
    Gets a device's logical name (e.g., "PACEMAKER-001") based on its port (e.g., "COM3").
    If the port is new and the 10-device limit isn't reached, it assigns a new name.
    """
    if not port_name:
        return "--" # Handle null port name
        
    devices = load_device_names()
    
    # 1. Check if this port is already known
    for device in devices:
        if device.get("port") == port_name:
            return device.get("name", port_name) # Return its saved name
            
    # 2. If new, check if we have space (max 10 devices)
    if len(devices) >= 10:
        return f"PORT-FULL ({port_name})" # Notify that the device list is full

    # 3. Find the next available number (e.g., if 001 and 003 exist, next is 004)
    max_num = 0
    for device in devices:
        try:
            # Extract the number part of "PACEMAKER-XXX"
            num = int(device.get("name", "PACEMAKER-000").split("-")[-1])
            max_num = max(max_num, num)
        except Exception:
            continue # Ignore malformed names
            
    new_name = f"PACEMAKER-{max_num + 1:03d}" # Format new name, e.g., PACEMAKER-004
    
    # 4. Add the new device to the list and save it
    devices.append({
        "port": port_name,
        "name": new_name
    })
    
    save_device_names(devices)
    return new_name