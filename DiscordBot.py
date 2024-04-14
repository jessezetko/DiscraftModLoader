import discord
from discord import app_commands
import requests
import re
from urllib.parse import urlparse, unquote
import os
import logging
import shutil

# API Key
API_KEY = '?'
# Discord bot token
TOKEN = '?'
# Discord GUILD
GUILD = 0
# Discord channel id
CHANNEL_ID = 0
# Mod directory
MOD_DIRECTORY = r''
# Game Version (Used for mod search)
GAME_VERSION = '1.20.1'
# server.js upload url
UPLOAD_URL = 'http://localhost:3000/upload'

# Setting up the Discord bot
intents = discord.Intents.all()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)
messageids = {"messageid" : 0}

@tree.command(name="modlist", description="Current modpack mods", guild=discord.Object(id=GUILD))
async def list_mods(interaction):
    # Check if the directory exists
    if not os.path.exists(MOD_DIRECTORY):
        await interaction.channel.send("Directory does not exist.")
        return
    
    # List all files in the directory
    file_names = os.listdir(MOD_DIRECTORY)
    file_list = "\n".join(file_names)

    # Send the list to the Discord channel
    # If the message is too long, it can be split into multiple messages
    max_length = 2000
    for i in range(0, len(file_list), max_length):
        await interaction.channel.send(file_list[i:i+max_length])
    await interaction.response.send_message("Modpack current mods:")

@tree.command(name="modsearch", description="Search for mods", guild=discord.Object(id=GUILD))
async def search_mods(interaction, search_filter: str):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'x-api-key': API_KEY
    }

    try:
      r = requests.get('https://api.curseforge.com/v1/mods/search', params={'gameId': 432, 'searchFilter': search_filter, 'gameVersions': GAME_VERSION, "sortOrder": "desc", "modLoaderType": 1, "classId": 6, "sortField": 6}, headers=headers)
      data = r.json().get('data', [])

      download_url = ""

      # Regular expression to find URLs
      url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
      match = re.search(url_pattern, search_filter)
      
      print ("Searching for mod: " + search_filter)

      if match:
        mod_url = match.group(0)  # Returns the first URL found
        print("URL search detected...")

      else:
        # Filter mods that have any file with game version GAME_VERSION
        filtered_data = []
        for mod in data:
                 # check latestfilesindexes if downloadurl not in latestfiles because this api is horrible
                if (str(search_filter).lower() in str(mod.get('displayName')).lower() or str(search_filter).lower() in str(mod.get('name')).lower()):
                    for fileindex in mod.get('latestFilesIndexes', []):
                        if "75125" in str(fileindex.get('gameVersionTypeId')) and "1" in str(fileindex.get("modLoader")):
                            download_url = "https://edge.forgecdn.net/files/" + str(fileindex.get('fileId'))[:4] + "/" + str(fileindex.get('fileId'))[len(str(fileindex.get('fileId'))) - 3:] + "/" + fileindex.get('filename')
                            break
                for latest_files in mod.get('latestFiles', []):
                    if download_url != "":
                        break
                    if GAME_VERSION in latest_files.get('gameVersions', []):
                        if "Forge" not in latest_files.get('gameVersions', []) or GAME_VERSION not in latest_files.get('gameVersions', []):
                            #print("incompatible mod " + mod.get('name'))
                            download_url = ""
                        else:
                            download_url = latest_files.get('downloadUrl') if latest_files.get('downloadUrl') else ""
                            if ".jar" not in download_url or (str(search_filter).lower() not in str(latest_files.get('displayName')).lower() or str(search_filter).lower() not in str(mod.get('name')).lower()):
                                #print("incompatible mod " + mod.get('name'))
                                download_url = ""
                            else:
                                print ("version and forge matched")
                                break
                        
    except:
        await interaction.response.send_message("No mod found")
        logging.exception("message")
        return

    if download_url == "": 
      await interaction.response.send_message(f'No mod found for Minecraft version {GAME_VERSION}')
      return

    msg = await interaction.channel.send("Download URL - " + download_url + "\nAdd file to Modpack?")
    #await interaction.channel.send("Mod Post URL - " + str(post_url))

    await msg.add_reaction('\u2705')  # Add a checkmark reaction to the message
    await msg.add_reaction('\u274C')  # Add a cross reaction to the message

    messageids["messageid"] = msg.id



# @tree.command(name="modfiles", description="Zips current working mod folder directory and uploads to website for download.", guild=discord.Object(id=GUILD))
# async def search_mods(interaction):
#     await interaction.response.defer()

#     folder_path = ''
#     zip_path = MOD_DIRECTORY

#     shutil.make_archive(zip_path, 'zip', folder_path)

#     await interaction.followup.send("Current mod files zipped and avaliable for download at websiteurl")


@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD))
    print("Ready!")

@bot.event
async def on_raw_reaction_add(reaction):
    #print("emoji reaction message id: " + str(reaction.message_id) + " trying to match " + str(messageids["messageid"]) + " reaction char: " + str(reaction.emoji))
    # Check if the reaction is what we are looking for
    if str(reaction.emoji) == '\u2705' and reaction.message_id == messageids["messageid"]: #checkmark match
        messageids["messageid"] = 0
        print("Adding mod to web server...")

        channel = bot.get_channel(CHANNEL_ID)

        # Get message containing mod url
        message = await channel.fetch_message(reaction.message_id)

       # Regular expression to find URL within message
        url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
        match = re.search(url_pattern, message.content)
        if match:
            file_url = match.group(0)  # Returns the first URL found

            # Parse the URL to get the path
            parsed_url = urlparse(file_url)
            path = parsed_url.path

            # Extract the filename from the path
            file_name = unquote(path.split('/')[-1])
        else:
            channel.send("Invalid download URL")
            return

        # download the .jar
        response = requests.get(file_url)
        if response.status_code == 200:
            with open('./uploads/' + file_name, 'wb') as file:
                file.write(response.content)

        # Prepare API request to server.js endpoint
        headers = {'x-api-key': API_KEY}
        files=[
          ('modFile',(file_name,open('./uploads/' + file_name,'rb'),'application/java-archive'))
        ]
        response = requests.post(UPLOAD_URL, headers=headers, data={},files=files)

        if response.status_code == 200:
            await channel.send("Modpack file added successfully! Be sure to add mod file from the url previously provided to your local Minecraft directory.")
        else:
            await channel.send("Failed to add modpack file. response code " + str(response.status_code) + " response info: " + str(response.text))
    if str(reaction.emoji) == '\u274C' and reaction.message_id == messageids["messageid"]: #x match
        messageids["messageid"] = 0
        channel = bot.get_channel(CHANNEL_ID)
        await channel.send("Mod not added to modpack.")

# Run the bot
bot.run(TOKEN)