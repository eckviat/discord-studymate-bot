import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name = "hello", 
        description = "發送訊息「Hello, world!」",
        extras={"example": "/hello"}
    )
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("👋 Hello, world!")

    @app_commands.command(
        name = "add", 
        description = "將整數 a 和整數 b 加總",
        extras={"example": "/add <a>123 <b>456"}
    )
    @app_commands.describe(a = "整數 a（必填）", b = "整數 b（必填）")
    async def add(self, interaction: discord.Interaction, a: int, b: int):
        await interaction.response.send_message(f"🔢 {a} + {b} = {a + b}")

    @app_commands.command(
        name = "say", 
        description = "讓機器人代替你說一些話",
        extras={"example": "/say [name]StudyMate [text]Hello, World"}
    )
    @app_commands.describe(name = "名稱（選填）", text = "訊息內容（選填）")
    async def say(self, interaction: discord.Interaction, name: Optional[str] = None, text:  Optional[str] = None):
        if name == None:
            name = "StudyMate"
        if text == None:
            text = "Coocoocoo!"
        await interaction.response.send_message(
            f"✅ 已發送訊息！\n\n{name} 說：\n「{text}」",
            ephemeral=True
        )

        await interaction.channel.send(f"📢 {name} 說：\n「{text}」")
        
async def setup(bot: commands.bot):
    await bot.add_cog(Misc(bot))