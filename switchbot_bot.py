import discord
from discord import app_commands
import time
import uuid
import hmac
import hashlib
import base64
import requests
import os

# Renderの環境変数から秘密の鍵を読み込む
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
ACCESS_TOKEN = os.environ.get("SWITCHBOT_TOKEN")
CLIENT_SECRET = os.environ.get("SWITCHBOT_SECRET")
DEVICE_ID = os.environ.get("SWITCHBOT_DEVICE_ID")

def make_switchbot_headers():
    nonce = str(uuid.uuid4())
    t = str(int(round(time.time() * 1000)))
    string_to_sign = f'{ACCESS_TOKEN}{t}{nonce}'
    string_to_sign = bytes(string_to_sign, 'utf-8')
    secret = bytes(CLIENT_SECRET, 'utf-8')
    sign = base64.b64encode(hmac.new(secret, msg=string_to_sign, digestmod=hashlib.sha256).digest())
    
    return {
        'Authorization': ACCESS_TOKEN,
        'API_Header': ACCESS_TOKEN,
        'Content-Type': 'application/json; charset=utf8',
        't': t,
        'sign': str(sign, 'utf-8'),
        'nonce': nonce
    }

def control_tape_light(command):
    url = f"https://api.switch-bot.com/v1.1/devices/{DEVICE_ID}/commands"
    headers = make_switchbot_headers()
    data = {
        "command": command,
        "parameter": "default",
        "commandType": "command"
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"API Error: {e}")
        return False

class MyBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f'Logged in as {self.user.name}')

bot = MyBot()

@bot.tree.command(name="light", description="テープライトのオン/オフを切り替えます")
@app_commands.choices(action=[
    app_commands.Choice(name="オン", value="turnOn"),
    app_commands.Choice(name="オフ", value="turnOff")
])
async def light_control(interaction: discord.Interaction, action: app_commands.Choice[str]):
    await interaction.response.defer()
    
    success = control_tape_light(action.value)
    
    status_text = "オン" if action.value == "turnOn" else "オフ"
    if success:
        await interaction.followup.send(f"テープライトを{status_text}にしました！")
    else:
        await interaction.followup.send("SwitchBot APIの呼び出しに失敗しました。環境変数やDevice IDを確認してください。")

if DISCORD_TOKEN:
    bot.run(DISCORD_TOKEN)
else:
    print("エラー: DISCORD_TOKEN が設定されていません。")
