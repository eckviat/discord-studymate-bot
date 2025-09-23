import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class Misc(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name = "hello", description = "Hello, world!")
    async def hello(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello, world!")

    @app_commands.command(name = "add", description = "Add 2 numbers")
    @app_commands.describe(a = "Number a", b = "Number b")
    async def add(self, interaction: discord.Interaction, a: int, b: int):
        await interaction.response.send_message(f"Total: {a + b}")

    @app_commands.command(name = "say", description = "Say something")
    @app_commands.describe(name = "Your name", text = "Say something")
    async def say(self, interaction: discord.Interaction, name: Optional[str] = None, text:  Optional[str] = None):
        if name == None:
            name = "StudyMate"
        if text == None:
            text = "Coocoocoo!"
        await interaction.response.send_message(f"{name} 說 「{text}」")
        
async def setup(bot: commands.bot):
    await bot.add_cog(Misc(bot))