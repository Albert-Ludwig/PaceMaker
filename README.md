Johnson's comments on each file

Folder File Purpose:

main.py Entry point: launches login screen and dashboard. The main file should only contains the welcome window class can call the interfaces from other files.

modules/auth.py Handles registration/login logic with password hashing

modules/dashboard.py Main DCM interface: mode selection, parameter input, status indicators

modules/storage.py Read/write JSON files for users and parameters

data/users.json Stores up to 10 registered users

data/parameters.json Stores saved parameter sets

assets/ Optional: icons, logos, style assets
