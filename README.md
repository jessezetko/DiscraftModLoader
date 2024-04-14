# DiscraftModLoader
This project includes a bot made for my discord server so that friends may search for and add mods to our Minecraft server with just a command and a node.js api service for uploading the files.

# Server.js
This is the api responsible for uploading new files to the modpack folder. An API key and upload directory will need to be configured.

# DiscordBot.py
This bot contains commands for listing currently installed mods, searching the curseforge api for mods & uploading files to the minecraft mod folder.
You will need to configure API_KEY, TOKEN, GUILD, CHANNEL_ID, MOD_DIRECTORY, & GAME_VERSION parameters at the beginning of the file.

# Setup instructions
1. Configure variables at start of Server.js & DiscordBot.py files
2. run 'npm install' & 'pip install -r requirements.txt'
3. run 'node Server.js'
4. run 'py DiscordBot.py'