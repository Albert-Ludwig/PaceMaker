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

# --- NEW: Device Name Management Functions ---

def _get_default_device_data():
    """Returns the default structure for the device JSON file."""
    return {
        "last_connected_device_name": None,
        "devices": []
    }

def load_device_names():
    """
    Loads the device data object { "last_...": "...", "devices": [...] }.
    Handles migration from the old list-based format automatically.
    """
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(DEVICE_FILE):
        data = _get_default_device_data()
        save_device_names(data)
        return data
    
    try:
        with open(DEVICE_FILE, "r") as f:
            data = json.load(f)
            
        # --- MIGRATION LOGIC ---
        # If the file is just a list (old format), convert it.
        if isinstance(data, list):
            migrated_data = _get_default_device_data()
            migrated_data["devices"] = data # Keep the old device list
            save_device_names(migrated_data)
            return migrated_data
        # --- END MIGRATION ---

        # Ensure keys exist if it's a dict but malformed
        if "devices" not in data:
            data["devices"] = []
        if "last_connected_device_name" not in data:
            data["last_connected_device_name"] = None

        return data
        
    except json.JSONDecodeError:
        return _get_default_device_data()

def save_device_names(device_data):
    """Saves the entire device data object back to the JSON file."""
    with open(DEVICE_FILE, "w") as f:
        json.dump(device_data, f, indent=2)

def get_last_connected_device():
    """Reads and returns only the 'last_connected_device_name' string."""
    device_data = load_device_names()
    return device_data.get("last_connected_device_name")

def set_last_connected_device(device_name: str):
    """Updates and saves the 'last_connected_device_name' string."""
    device_data = load_device_names()
    device_data["last_connected_device_name"] = device_name
    save_device_names(device_data)

def get_or_assign_device_name(port_name: str) -> str:
    """
    Gets a device's logical name based on its port.
    If the port is new, it assigns a new name and saves it.
    """
    if not port_name:
        return "--"
        
    device_data = load_device_names()
    devices_list = device_data.get("devices", [])
    
    # 1. Check if this port is already known
    for device in devices_list:
        if device.get("port") == port_name:
            return device.get("name", port_name)
            
    # 2. If new, check if we have space (max 10 devices)
    if len(devices_list) >= 10:
        return f"PORT-FULL ({port_name})"

    # 3. Find the next available number
    max_num = 0
    for device in devices_list:
        try:
            num = int(device.get("name", "PACEMAKER-000").split("-")[-1])
            max_num = max(max_num, num)
        except Exception:
            continue
            
    new_name = f"PACEMAKER-{max_num + 1:03d}"
    
    # 4. Add the new device to the list and save the whole object
    devices_list.append({
        "port": port_name,
        "name": new_name
    })
    device_data["devices"] = devices_list
    
    save_device_names(device_data)
    return new_name