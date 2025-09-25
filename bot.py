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
guild = discord.Object(id=GUILD_ID)

# ========= 定義 MyBot =========
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.voice_states = True         # 允許追蹤語音頻道事件
        intents.messages = True              
        intents.message_content = True      # 允許讀取訊息內容
        super().__init__(command_prefix="!coo ", intents=intents)
            
    async def setup_hook(self):
        # 載入 Cogs
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py") and not filename.startswith("_"):
                ext = f"cogs.{filename[:-3]}"
                try:
                    await self.load_extension(ext)
                    print(f"✅ 已載入 {ext}")
                except Exception as e:
                    print(f"❌ 載入 {ext} 失敗: {e}")

        # 把全域指令複製到指定伺服器
        self.tree.copy_global_to(guild=guild)
        
        # 同步 slash 指令到伺服器
        synced = await self.tree.sync(guild=guild)
        print(f"🔧 {len(synced)} slash commands synced to guild {GUILD_ID}")

    async def on_ready(self):
        print(f"✅ 已登入：{self.user} (ID: {self.user.id})")

    async def on_message(self, message: discord.Message):
        # 避免機器人自己觸發
        if message.author.bot:
            return
        # 確保文字指令會正確被處理
        await self.process_commands(message)

bot = MyBot()
bot.remove_command("help")

# ========= 管理指令 =========
@bot.command(name="reload_cog")
@commands.is_owner()
async def reload_cog(ctx, cog: str):
    """重新載入特定 Cog"""
    ext = f"cogs.{cog}"
    try:
        if ext in bot.extensions:
            await bot.unload_extension(f"cogs.{cog}")
        await bot.load_extension(f"cogs.{cog}")
        await ctx.send(f"🔄️ `{ext}` 重新載入成功！")
    except Exception as e:
        await ctx.send(f"❌ `{ext}` 重新載入失敗：`{e}`")
    
    # 把全域指令複製到指定伺服器
    bot.tree.copy_global_to(guild=guild)
    
    # 同步斜線指令到伺服器
    synced = await bot.tree.sync(guild=guild)
    await ctx.send(f"🔄️ {len(synced)} slash commands synced to guild.")

@bot.command(name="reload_all")
@commands.is_owner()
async def reload_all(ctx):
    """重新載入所有 Cogs"""
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            ext = f"cogs.{filename[:-3]}"
            try:
                if ext in bot.extensions:
                    await bot.unload_extension(ext)
                await bot.load_extension(ext)
                await ctx.send(f"🔄️ `{ext}` 重新載入成功！")
            except Exception as e:
                await ctx.send(f"❌ `{ext}` 重新載入失敗：`{e}`")
    
    # 把全域指令複製到指定伺服器
    bot.tree.copy_global_to(guild=guild)
    
    # 同步斜線指令到伺服器
    synced = await bot.tree.sync(guild=guild)
    await ctx.send(f"🔄️ {len(synced)} slash commands synced to guild.")

@bot.command(name="list_cogs")
async def list_cogs(ctx):
    """列出所有目前已載入的 Cogs"""
    if bot.extensions:
        loaded = "\n".join(bot.extensions.keys())
        await ctx.send(f"📚 目前已載入的 Cogs：\n```\n{loaded}\n```")
    else:
        await ctx.send("⚠️ 目前沒有載入任何 Cogs")

# ========= 啟動 =========
if __name__ == "__main__":
    async def main():
        async with bot:
            await bot.start(TOKEN)
    asyncio.run(main())