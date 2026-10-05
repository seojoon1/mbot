import os
import sqlite3
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
DB_PATH = os.getenv("DB_PATH", "mbot.db")
# 경고가 이 횟수에 도달할 때마다 타임아웃
WARN_LIMIT = int(os.getenv("WARN_LIMIT", "3"))
TIMEOUT_MINUTES = int(os.getenv("TIMEOUT_MINUTES", "10"))


# ---------- DB ----------
db = sqlite3.connect(DB_PATH)
db.execute(
    """CREATE TABLE IF NOT EXISTS warnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        moderator_id INTEGER NOT NULL,
        reason TEXT NOT NULL,
        created_at TEXT NOT NULL
    )"""
)
db.execute(
    """CREATE TABLE IF NOT EXISTS banned_words (
        guild_id INTEGER NOT NULL,
        word TEXT NOT NULL,
        PRIMARY KEY (guild_id, word)
    )"""
)
db.commit()


def add_warning(guild_id: int, user_id: int, moderator_id: int, reason: str) -> int:
    db.execute(
        "INSERT INTO warnings (guild_id, user_id, moderator_id, reason, created_at) VALUES (?, ?, ?, ?, ?)",
        (guild_id, user_id, moderator_id, reason, datetime.now(timezone.utc).isoformat()),
    )
    db.commit()
    return count_warnings(guild_id, user_id)


def count_warnings(guild_id: int, user_id: int) -> int:
    return db.execute(
        "SELECT COUNT(*) FROM warnings WHERE guild_id = ? AND user_id = ?", (guild_id, user_id)
    ).fetchone()[0]


def list_warnings(guild_id: int, user_id: int):
    return db.execute(
        "SELECT id, moderator_id, reason, created_at FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY id",
        (guild_id, user_id),
    ).fetchall()


def get_banned_words(guild_id: int) -> list[str]:
    rows = db.execute("SELECT word FROM banned_words WHERE guild_id = ?", (guild_id,)).fetchall()
    return [r[0] for r in rows]


def normalize(text: str) -> str:
    # 공백/일부 특수문자로 우회하는 것 방지 (예: "바 보", "바.보")
    return "".join(ch for ch in text.lower() if ch.isalnum())


# ---------- Bot ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class ModBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


bot = ModBot()


async def apply_warning(member: discord.Member, moderator: discord.abc.User, reason: str, channel) -> int:
    count = add_warning(member.guild.id, member.id, moderator.id, reason)
    msg = f"⚠️ {member.mention} 경고 {count}회 (사유: {reason})"
    if count % WARN_LIMIT == 0:
        try:
            await member.timeout(timedelta(minutes=TIMEOUT_MINUTES), reason=f"경고 {count}회 누적")
            msg += f"\n⏱️ 경고 누적으로 {TIMEOUT_MINUTES}분 타임아웃"
        except discord.Forbidden:
            msg += "\n(타임아웃 권한이 없어 타임아웃하지 못했습니다)"
    await channel.send(msg)
    return count


@bot.event
async def on_ready():
    print(f"로그인: {bot.user} (id={bot.user.id})")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or message.guild is None:
        return
    # 관리자는 검열 대상에서 제외
    if message.author.guild_permissions.manage_messages:
        return

    content = normalize(message.content)
    hit = next((w for w in get_banned_words(message.guild.id) if normalize(w) in content), None)
    if hit is None:
        return

    try:
        await message.delete()
    except discord.Forbidden:
        pass
    await apply_warning(message.author, bot.user, f"금지어 사용", message.channel)


# ---------- 경고 명령어 ----------
@bot.tree.command(name="경고", description="유저에게 경고를 줍니다")
@app_commands.describe(유저="경고할 유저", 사유="경고 사유")
@app_commands.default_permissions(moderate_members=True)
@app_commands.guild_only()
async def warn(interaction: discord.Interaction, 유저: discord.Member, 사유: str = "사유 없음"):
    if 유저.bot:
        await interaction.response.send_message("봇에게는 경고할 수 없습니다.", ephemeral=True)
        return
    await interaction.response.send_message("경고를 부여했습니다.", ephemeral=True)
    await apply_warning(유저, interaction.user, 사유, interaction.channel)


@bot.tree.command(name="경고목록", description="유저의 경고 내역을 봅니다")
@app_commands.default_permissions(moderate_members=True)
@app_commands.guild_only()
async def warnings(interaction: discord.Interaction, 유저: discord.Member):
    rows = list_warnings(interaction.guild.id, 유저.id)
    if not rows:
        await interaction.response.send_message(f"{유저.display_name}님은 경고가 없습니다.", ephemeral=True)
        return
    embed = discord.Embed(title=f"{유저.display_name}님의 경고 ({len(rows)}회)", color=discord.Color.orange())
    for wid, mod_id, reason, created_at in rows[-25:]:
        date = created_at[:10]
        embed.add_field(name=f"#{wid} · {date}", value=f"{reason}\n담당: <@{mod_id}>", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="경고삭제", description="경고를 삭제합니다 (번호 생략 시 전체 초기화)")
@app_commands.describe(번호="삭제할 경고 번호 (/경고목록에서 확인)")
@app_commands.default_permissions(moderate_members=True)
@app_commands.guild_only()
async def clear_warning(interaction: discord.Interaction, 유저: discord.Member, 번호: int | None = None):
    if 번호 is None:
        cur = db.execute("DELETE FROM warnings WHERE guild_id = ? AND user_id = ?", (interaction.guild.id, 유저.id))
    else:
        cur = db.execute(
            "DELETE FROM warnings WHERE id = ? AND guild_id = ? AND user_id = ?",
            (번호, interaction.guild.id, 유저.id),
        )
    db.commit()
    await interaction.response.send_message(
        f"{유저.display_name}님의 경고 {cur.rowcount}건을 삭제했습니다.", ephemeral=True
    )


# ---------- 금지어 명령어 ----------
banned = app_commands.Group(
    name="금지어",
    description="금지어 관리",
    default_permissions=discord.Permissions(manage_messages=True),
    guild_only=True,
)


@banned.command(name="추가", description="금지어를 추가합니다")
async def banned_add(interaction: discord.Interaction, 단어: str):
    if not normalize(단어):
        await interaction.response.send_message("유효한 단어를 입력해주세요.", ephemeral=True)
        return
    db.execute("INSERT OR IGNORE INTO banned_words (guild_id, word) VALUES (?, ?)", (interaction.guild.id, 단어))
    db.commit()
    await interaction.response.send_message(f"금지어 추가: ||{단어}||", ephemeral=True)


@banned.command(name="삭제", description="금지어를 삭제합니다")
async def banned_remove(interaction: discord.Interaction, 단어: str):
    cur = db.execute("DELETE FROM banned_words WHERE guild_id = ? AND word = ?", (interaction.guild.id, 단어))
    db.commit()
    msg = f"금지어 삭제: ||{단어}||" if cur.rowcount else "등록되지 않은 단어입니다."
    await interaction.response.send_message(msg, ephemeral=True)


@banned.command(name="목록", description="금지어 목록을 봅니다")
async def banned_list(interaction: discord.Interaction):
    words = get_banned_words(interaction.guild.id)
    text = ", ".join(f"||{w}||" for w in words) if words else "등록된 금지어가 없습니다."
    await interaction.response.send_message(text[:2000], ephemeral=True)


bot.tree.add_command(banned)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit(".env 파일에 DISCORD_TOKEN을 설정하세요.")
    bot.run(TOKEN)
