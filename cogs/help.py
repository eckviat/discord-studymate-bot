# cogs/help.py
import discord
from discord.ext import commands
from discord import app_commands
import inspect
from typing import Optional, Union, get_origin, get_args

# 處理參數格式
def format_param(name: str, param: inspect.Parameter) -> str:
    ann = param.annotation
    type_name = "str"  # 預設
    required = True

    if ann is not inspect._empty:
        origin = get_origin(ann)
        if origin is Union:  # Optional[str] -> Union[str, NoneType]
            args = [a for a in get_args(ann) if a is not type(None)]
            if args:
                type_name = getattr(args[0], "__name__", str(args[0]))
            required = False
        else:
            type_name = getattr(ann, "__name__", str(ann))

    if param.default is not inspect._empty:
        required = False

    if required:
        return f"{name}:{type_name}"
    else:
        return f"(選填) {name}:{type_name}"

def build_command_description(cmd: app_commands.Command) -> str:
    # 解析 callback 參數
    try:
        sig = inspect.signature(cmd.callback)
        parts = []
        for name, p in sig.parameters.items():
            if name in ("self", "interaction"):
                continue
            parts.append(format_param(name, p))
        params_str = " | ".join(parts) if parts else "無參數"
    except Exception:
        params_str = "無參數"

    # 範例：extras["example"]
    example = cmd.extras.get("example", f"/{cmd.qualified_name} ...")

    return (
        f"/{cmd.qualified_name}\n"
        f"　說明：{cmd.description or '沒有說明'}\n"
        f"　參數：{params_str}\n"
        f"　範例：{example}"
    )

# 下拉選單
class HelpSelect(discord.ui.Select):
    def __init__(self, grouped):
        options = [
            discord.SelectOption(label=cog, description=f"{len(cmds)} 個指令")
            for cog, cmds in grouped.items()
        ]
        super().__init__(placeholder="選擇要查看的分類…", options=options)
        self.grouped = grouped

    async def callback(self, interaction: discord.Interaction):
        cog = self.values[0]
        embed = discord.Embed(
            title=f"📂 {cog} 指令",
            color=discord.Color.blurple()
        )
        value_lines = []
        for cmd in self.grouped[cog]:
            value_lines.append(build_command_description(cmd))
        embed.description = "\n\n".join(value_lines)
        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, grouped, timeout=120):
        super().__init__(timeout=timeout)
        self.add_item(HelpSelect(grouped))

# Cog
class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="help", 
        description="查看所有可用的斜線指令",
        extras={"example": "/help"}
    )
    async def help_command(self, interaction: discord.Interaction):
        # 分類
        grouped = {}
        for cmd in self.bot.tree.walk_commands():
            if not isinstance(cmd, app_commands.Command):
                continue
            cog_name = cmd.binding.__cog_name__ if hasattr(cmd, "binding") else "未分類"
            grouped.setdefault(cog_name, []).append(cmd)

        embed = discord.Embed(
            title="📖 指令總覽",
            description="請從下拉選單中選擇一個分類",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, view=HelpView(grouped), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
