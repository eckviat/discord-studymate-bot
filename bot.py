import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import os

# ========= 載入 .env =========
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID_ENV = os.getenv("GUILD_ID", "").strip()
GUILD_ID = int(GUILD_ID_ENV) if GUILD_ID_ENV.isdigit() else None

# ========= 定義 MyBot =========
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True         # 允許追蹤語音頻道事件
        intents.message_content = True      # 允許讀取訊息內容
        super().__init__(command_prefix="", intents=intents)
            
    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)

        # 載入 Cogs
        await self.load_extension("cogs.misc")
        await self.load_extension("cogs.study")
        
        # 把全域指令複製到指定伺服器
        self.tree.copy_global_to(guild=guild)
        
        # 同步 slash 指令到伺服器
        synced = await self.tree.sync(guild=guild)
        print(f"🔧 {len(synced)} slash commands synced to guild {GUILD_ID}")

    async def on_ready(self):
        print(f"✅ 已登入：{self.user} (ID: {self.user.id})")

bot = MyBot()

# ========= 啟動 =========
if __name__ == "__main__":
    async def main():
        async with bot:
            await bot.start(TOKEN)
    asyncio.run(main())