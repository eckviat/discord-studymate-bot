import os
import json
import asyncio
from datetime import datetime, timedelta
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

# ========= 資料結構 =========
sessions = {}   # user_id -> {start, end, project, notify_channel_id, task}
SEATS = [chr(ord('A') + i) for i in range(9)]  # A~I
seat_assign = {}
LOG_FILE = "learning_log.json"

# =========== 存檔 ===========
def save_log(user_id: int, username: str, project: str, start: datetime, end: datetime, minutes: int):
    record = {
        "user_id": user_id,
        "username": username,
        "project": project,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "minutes": minutes,
    }
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        data.append(record)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("save_log error:", e)
        
# ========= 顯示座位 =========
async def render_seat_map(bot: commands.Bot) -> str:
    lines = []
    # 黑板 + 講台
    lines.append("──────────────────── Board ────────────────────")
    lines.append("┌───────────────────────┐")
    lines.append("│         Stage         │")
    lines.append("└───────────────────────┘")

    for r in range(3):
        top = []
        mid = []
        bot_line = []
        for c in range(3):
            seat = SEATS[r*3 + c]
            occ = None
            for uid, s in seat_assign.items():
                if s == seat:
                    u = bot.get_user(uid)
                    if not u:
                        try:
                            u = await bot.fetch_user(uid)
                        except:
                            pass
                    occ = (str(u) if u else f"{str(uid)[-4:]}")[:4]
                    break

            # 格子設計
            top.append("┌────────┐")
            if occ:
                mid.append(f"│ {seat}:{occ:<4} │")
            else:
                mid.append(f"│ {seat}:____ │")
            bot_line.append("└────────┘")

        # 拼接成一排
        lines.append("   ".join(top))
        lines.append("   ".join(mid))
        lines.append("   ".join(bot_line))

    # 取得最大行長度
    max_len = max(len(line) for line in lines)

    # 每行置中對齊
    centered_lines = [line.center(max_len) for line in lines]

    return "\n".join(centered_lines)

# ========= 建立計時器 =========
async def schedule_reminder(bot: commands.Bot, user_id: int):
    old = sessions[user_id].get("task")
    if old and not old.done():
        old.cancel()

    async def _task():
        while True:
            now = datetime.now()
            end = sessions[user_id]["end"]
            remain = (end - now).total_seconds()
            if remain <= 0:
                break
            await asyncio.sleep(min(30, remain))

        sess = sessions.get(user_id)
        if not sess:
            return
        user = bot.get_user(user_id) or await bot.fetch_user(user_id)
        start = sess["start"]
        end = datetime.now()
        minutes = max(1, int((end - start).total_seconds() // 60))
        project = sess["project"]

        seat_assign.pop(user_id, None)
        sessions.pop(user_id, None)

        seatmap_str = await render_seat_map(bot)
        ch = bot.get_channel(sess["notify_channel_id"])
        if ch:
            await ch.send(
                f"⏰ {user.mention} 自習時間結束，實際學習{format_project(project)} {minutes} 分鐘。\n"
                f"🪑 目前座位表：\n```\n{seatmap_str}\n```"
            )

        await user.send(f"⏰ 你的自習時間到囉！實際學習{format_project(project)} {minutes} 分鐘。")

        save_log(user_id, user.name if user else str(user_id), sess["project"], start, end, minutes)

    sessions[user_id]["task"] = asyncio.create_task(_task())

# =========== 格式化輸出 ===========
def format_project(project: Optional[str]) -> str:
    return f" **{project}**" if project else ""

# =========== 指令 ===========
class Study(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    # =========== 開始計時學習時間 ===========
    @app_commands.command(name="start_learning", description="開始自習")
    @app_commands.describe(duration="學習時間（分鐘）", project="學習項目（選填）")
    async def start_learning(self, interaction: discord.Interaction, duration: int, project: Optional[str] = None):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ 你需要先進入語音頻道才能開始自習。", ephemeral=True)
            return
        if duration <= 0:
            await interaction.response.send_message("❌ duration 需為正整數。", ephemeral=True)
            return
        if interaction.user.id in sessions:
            await interaction.response.send_message("⚠️ 你已經在自習中，使用 `/add_learning_time` 來增加自習時間，或 `/finish_learning` 來結束自習。", ephemeral=True)
            return
    
        start = datetime.now()
        end = start + timedelta(minutes=duration)
        sessions[interaction.user.id] = {
            "start": start,
            "end": end,
            "project": project,
            "notify_channel_id": interaction.channel.id,
            "task": None,
        }
    
        used = set(seat_assign.values())
        seat = next((s for s in SEATS if s not in used), None)
        if seat is None:
            seat_text = "（座位已滿，暫無法入座）"
        else:
            seat_assign[interaction.user.id] = seat
            seat_text = f"🪑 你已入座 **{seat}**。"

        seatmap_str = await render_seat_map(self.bot)

        await interaction.response.send_message(
            f"📚 {interaction.user.mention} 開始學習{format_project(project)} {duration} 分鐘。\n"
            f"{seat_text}\n\n🪑 目前座位表：\n```\n{seatmap_str}\n```"
        )
        await schedule_reminder(self.bot, interaction.user.id)
    
    # =========== 延長學習時間 ===========
    @app_commands.command(name="add_learning_time", description="延長自習時間")
    @app_commands.describe(time="延長的分鐘數")
    async def add_learning_time(self, interaction: discord.Interaction, time: int):
        if interaction.user.id not in sessions:
            await interaction.response.send_message("⚠️ 你沒有正在進行的自習。", ephemeral=True)
            return
        sessions[interaction.user.id]["end"] += timedelta(minutes=time)
        await interaction.response.send_message(f"⏫ 已為你延長 {time} 分鐘。")
        await schedule_reminder(self.bot, interaction.user.id)
    
    # =========== 編輯學習資訊 ===========
    @app_commands.command(name="edit_information", description="編輯學習時間或項目")
    @app_commands.describe(duration="學習時間（分鐘）", project="學習項目")
    async def edit_information(self, interaction: discord.Interaction, duration: Optional[int] = None, project: Optional[str] = None):
        if interaction.user.id not in sessions:
            await interaction.response.send_message("⚠️ 你沒有正在進行的自習。", ephemeral=True)
            return
        
        sess = sessions[interaction.user.id]
        old_project = sess["project"]
        old_end = sess["end"]
    
        if duration is not None:
            if duration <= 0:
                await interaction.response.send_message("❌ duration 需為正整數。", ephemeral=True)
                return
            sess["end"] = sess["start"] + timedelta(minutes=duration)
        
        if project is not None:
            sess["project"] = project
        
        await schedule_reminder(self.bot, interaction.user.id)

        minutes = max(1, int((sess['end'] - sess['start']).total_seconds() // 60))
        await interaction.response.send_message(
            f"✏️ {interaction.user.mention} 已更新自習資訊。\n"
            f"📚 已改為學習{format_project(sess['project'])} {minutes} 分鐘。\n"
        )

    # =========== 結束學習 ===========
    @app_commands.command(name="finish_learning", description="結束自習並紀錄時數")
    async def finish_learning(self, interaction: discord.Interaction):
        sess = sessions.pop(interaction.user.id, None)
        if not sess:
            await interaction.response.send_message("⚠️ 你沒有正在進行的自習。", ephemeral=True)
            return
        
        task = sess.get("task")
        if task and not task.done():
            task.cancel()

        start = sess["start"]
        end = datetime.now()
        minutes = max(1, int((end - start).total_seconds() // 60))
        project = sess["project"]
        seat_assign.pop(interaction.user.id, None)
        user = interaction.user
        save_log(user.id, user.name, project, start, end, minutes)

        seatmap_str = await render_seat_map(self.bot)
        await interaction.response.send_message(
            f"⏰ {user.mention} 結束自習，實際學習{format_project(project)} {minutes} 分鐘。\n"
            f"🪑 目前座位表：\n```\n{seatmap_str}\n```"
        )
    
    # =========== 退出語音時停止自習 ===========
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # 如果使用者沒有正在自習，忽略
        if member.id not in sessions:
            return

        # before.channel != None 表示「原本在語音」
        # after.channel == None 表示「已經離開語音」
        if before.channel is not None and after.channel is None:
            sess = sessions.pop(member.id, None)
            if not sess:
                return

            task = sess.get("task")
            if task and not task.done():
                task.cancel()

            start = sess["start"]
            end = datetime.now()
            minutes = max(1, int((end - start).total_seconds() // 60))
            project = sess["project"]

            seat_assign.pop(member.id, None)
            save_log(member.id, member.name, project, start, end, minutes)

            seatmap_str = await render_seat_map(self.bot)

            # 公告到 notify_channel
            ch = self.bot.get_channel(sess["notify_channel_id"])
            if ch:
                await ch.send(
                    f"🚶 {member.mention} 已離開語音，自動結束自習，實際學習{format_project(project)} {minutes} 分鐘。\n"
                    f"🪑 目前座位表：\n```\n{seatmap_str}\n```"
                )

    # =========== 查看座位表 ===========
    @app_commands.command(name="seatmap", description="查看目前座位表")
    async def seatmap(self, interaction: discord.Interaction):
        seatmap_str = await render_seat_map(self.bot)
        await interaction.response.send_message(f"目前座位表：\n```\n{seatmap_str}\n```", ephemeral=True)
    
    # =========== 查看狀態、剩餘學習時間 ===========
    @app_commands.command(name="status", description="查看剩餘時間")
    async def status(self, interaction: discord.Interaction):
        sess = sessions.get(interaction.user.id)
        if not sess:
            await interaction.response.send_message("你沒有在自習喔。", ephemeral=True)
            return
        remain = int((sess["end"] - datetime.now()).total_seconds() // 60)
        await interaction.response.send_message(
            f"⏳ 項目：**{sess['project']}**，剩餘 {max(0, remain)} 分鐘。",
            ephemeral=True
        )

# ========= 啟動 =========
async def setup(bot: commands.Bot):
    await bot.add_cog(Study(bot))
