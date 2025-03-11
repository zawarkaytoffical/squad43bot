import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
import random
from discord.ui import Button, View
import pyrebase
import asyncio
import signal
from datetime import datetime, timedelta
import time
import requests
import googletrans
from googleapiclient.discovery import build
import yt_dlp as youtube_dl
from collections import deque
import logging
import aiohttp  # Для асинхронных HTTP-запросов

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord_bot')

load_dotenv()

TOKEN = MTMzODA4NDE5MzY0ODc3NTIzOQ.GcYB7k.WHmglnv06f1YFKIGuo1Ij7dDVzyZMisOyH2KZs
GUILD_ID = 1325093892718334094
STATUS_CHANNEL_ID = 1348383747149664499
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")
FFMPEG_PATH = os.getenv("FFMPEG_PATH")

if not FFMPEG_PATH or not os.path.exists(FFMPEG_PATH):
    raise Exception("Ошибка: Путь к ffmpeg не указан в .env или файл не найден! Укажи FFMPEG_PATH в .env.")

firebase_config = {
    "apiKey": "AIzaSyDsKgDj0XZjsk7akq8bl2I4BeL7M2uZgos",
    "authDomain": "ethereal-app-440213-a7.firebaseapp.com",
    "databaseURL": "https://ethereal-app-440213-a7-default-rtdb.europe-west1.firebasedatabase.app",
    "projectId": "ethereal-app-440213-a7",
    "storageBucket": "ethereal-app-440213-a7.firebasestorage.app",
    "messagingSenderId": "816579441359",
    "appId": "1:816579441359:web:8c75d77f3c887223777dba",
    "measurementId": "G-1HZDKEG5QF"
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=["43 ", "/"], intents=intents)
start_time = time.time()

music_queues = {}
looping = {}

youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'force-ipv4': True,
    'retries': 10,
    'fragment_retries': 10,
    'buffer_size': '64K',
    'extractor_retries': 10,  # Добавлено для улучшения обработки
    'http_headers': {         # Добавлены заголовки для обхода ограничений
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': '*/*',
    },
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

async def send_disconnect_message():
    status_channel = bot.get_channel(STATUS_CHANNEL_ID)
    if status_channel:
        embed = discord.Embed(
            title="💤 Бот отключился",
            description=f"{bot.user.name} ушёл в оффлайн.",
            color=discord.Color.red()
        )
        embed.add_field(name="Время", value=discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
        embed.set_thumbnail(url=bot.user.avatar.url)
        embed.set_footer(text="Squad #43 | Бот оффлайн")
        await status_channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild:
        print(f"Бот подключён к: {guild.name} (ID: {guild.id})")
    
    activity = discord.Activity(type=discord.ActivityType.playing, name="43 commands")
    await bot.change_presence(activity=activity)
    
    status_channel = bot.get_channel(STATUS_CHANNEL_ID)
    if status_channel:
        embed = discord.Embed(
            title="🚀 Бот запущен!",
            description=f"{bot.user.name} подключился к Squad #43!",
            color=discord.Color.green()
        )
        embed.add_field(name="Сервер", value=guild.name, inline=False)
        embed.add_field(name="Время", value=discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
        embed.set_thumbnail(url=bot.user.avatar.url)
        embed.set_footer(text="Squad #43 | Бот онлайн!")
        await status_channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if bot.user in message.mentions and not any(message.content.startswith(prefix) for prefix in bot.command_prefix):
        response = random.choice(["да", "нет", "хз", "никогда", "возможно", "https://cdn.discordapp.com/attachments/1345620407121744043/1348377515940642896/Baby_Two_Time.png"])
        await message.channel.send(response)
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    if member.guild.id == GUILD_ID:
        embed = discord.Embed(
            title="👋 Добро пожаловать в Squad #43!",
            description="Ты в Squad #43 — месте для творчества и общения.\n🔢 Мы не 42, мы 43 — идея @aukeu.\n😇 Уважай своих!",
            color=discord.Color.blue()
        )
        embed.add_field(name="🔗 Сайт", value="[squad43.site](https://squad43.site/)", inline=False)
        embed.set_footer(text="Squad #43 | Творчество и свобода!")
        try:
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id != bot.user.id:
        return
    
    if before.channel is not None and after.channel is None:
        guild_id = before.channel.guild.id
        if guild_id in music_queues:
            music_queues[guild_id]['queue'].clear()
            music_queues.pop(guild_id, None)
            looping.pop(guild_id, None)
        logger.info(f"Бот был отключён из голосового канала на сервере {guild_id}")

class CommandsView(View):
    def __init__(self, pages, ctx):
        super().__init__()
        self.pages = pages
        self.current_page = 0
        self.ctx = ctx
        self.message = None

    async def update_message(self):
        embed = self.pages[self.current_page]
        self.prev_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page == len(self.pages) - 1)
        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Назад", style=discord.ButtonStyle.grey)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message()
            await interaction.response.defer()

    @discord.ui.button(label="Вперёд", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.update_message()
            await interaction.response.defer()

@bot.command(name="commands")
async def commands_list(ctx):
    command_fields = [
        {"name": "43 commands или /commands", "value": "Список команд", "inline": False},
        {"name": "43 ban или /ban", "value": "Забанить (43 ban @User [причина])", "inline": False},
        {"name": "43 kick или /kick", "value": "Выгнать (43 kick @User [причина])", "inline": False},
        {"name": "43 mute или /mute", "value": "Замутить (43 mute @User [причина])", "inline": False},
        {"name": "43 unban или /unban", "value": "Разбанить (43 unban ID [причина])", "inline": False},
        {"name": "43 unmute или /unmute", "value": "Размутить (43 unmute @User [причина])", "inline": False},
        {"name": "43 warn или /warn", "value": "Варн (43 warn @User [причина])", "inline": False},
        {"name": "43 unwarn или /unwarn", "value": "Удалить варн (43 unwarn @User [all])", "inline": False},
        {"name": "43 warns или /warns", "value": "Список варнов (43 warns @User)", "inline": False},
        {"name": "43 ping или /ping", "value": "Пинг бота", "inline": False},
        {"name": "43 info или /info", "value": "Инфо о пользователе (43 info @User)", "inline": False},
        {"name": "43 serverinfo или /serverinfo", "value": "Инфо о сервере", "inline": False},
        {"name": "43 clear или /clear", "value": "Очистить (43 clear 10)", "inline": False},
        {"name": "43 roll или /roll", "value": "Кубик (43 roll или 43 roll 1-100)", "inline": False},
        {"name": "43 say или /say", "value": "Повторить (43 say Привет)", "inline": False},
        {"name": "43 coin или /coin", "value": "Монетка", "inline": False},
        {"name": "43 uptime или /uptime", "value": "Время работы", "inline": False},
        {"name": "43 remind или /remind", "value": "Напоминание (43 remind 30m Собрание)", "inline": False},
        {"name": "43 8ball или /8ball", "value": "Шар (43 8ball Дождь?)", "inline": False},
        {"name": "43 quote или /quote", "value": "Цитата", "inline": False},
        {"name": "43 roast или /roast", "value": "Поджарить (43 roast @User)", "inline": False},
        {"name": "43 leaderboard или /leaderboard", "value": "Топ (43 leaderboard warns)", "inline": False},
        {"name": "43 shoutout или /shoutout", "value": "Похвала (43 shoutout @User Текст)", "inline": False},
        {"name": "43 weather или /weather", "value": "Погода (43 weather Москва)", "inline": False},
        {"name": "43 translate или /translate", "value": "Перевод (43 translate ru Hello)", "inline": False},
        {"name": "43 search или /search", "value": "Поиск (43 search Squad #43)", "inline": False},
        {"name": "43 play или /play", "value": "Играть музыку (43 play URL)", "inline": False},
        {"name": "43 queue или /queue", "value": "Добавить в очередь (43 queue URL)", "inline": False},
        {"name": "43 skip или /skip", "value": "Пропустить трек", "inline": False},
        {"name": "43 volume или /volume", "value": "Изменить громкость (43 volume 50)", "inline": False},
        {"name": "43 nowplaying или /nowplaying", "value": "Инфо о текущем треке", "inline": False},
        {"name": "43 playlist или /playlist", "value": "Воспроизвести плейлист (43 playlist URL)", "inline": False},
        {"name": "43 shuffle или /shuffle", "value": "Перемешать очередь", "inline": False},
        {"name": "43 loop или /loop", "value": "Зациклить трек (43 loop)", "inline": False},
        {"name": "43 speed или /speed", "value": "Изменить скорость (43 speed 1.5)", "inline": False},
        {"name": "43 stop или /stop", "value": "Остановить музыку", "inline": False},
        {"name": "43 pause или /pause", "value": "Поставить на паузу", "inline": False},
        {"name": "43 resume или /resume", "value": "Возобновить воспроизведение", "inline": False},
        {"name": "43 clearqueue или /clearqueue", "value": "Очистить очередь", "inline": False},
        {"name": "43 viewqueue или /viewqueue", "value": "Просмотреть очередь", "inline": False},
        {"name": "43 remove или /remove", "value": "Удалить песню из очереди (43 remove номер)", "inline": False},
    ]

    items_per_page = 5
    pages = []
    for i in range(0, len(command_fields), items_per_page):
        embed = discord.Embed(title="📜 Команды Squad #43", description="Список команд (префиксы: `43 ` или `/`):", color=discord.Color.green())
        for field in command_fields[i:i + items_per_page]:
            embed.add_field(name=field["name"], value=field["value"], inline=field["inline"])
        embed.set_footer(text=f"Страница {len(pages) + 1}/{((len(command_fields) - 1) // items_per_page) + 1}")
        pages.append(embed)

    view = CommandsView(pages, ctx)
    view.message = await ctx.send(embed=pages[0], view=view)

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="Не указана"):
    await member.ban(reason=reason)
    embed = discord.Embed(title="🔨 Бан", description=f"{member.mention} забанен.\n**Причина:** {reason}", color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command()
async def penis(ctx):
    await ctx.send("penis")    

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="Не указана"):
    await member.kick(reason=reason)
    embed = discord.Embed(title="👢 Кик", description=f"{member.mention} выгнан.\n**Причина:** {reason}", color=discord.Color.orange())
    await ctx.send(embed=embed)

@bot.command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, *, reason="Не указана"):
    guild = ctx.guild
    muted_role = discord.utils.get(guild.roles, name="Muted")
    if not muted_role:
        muted_role = await guild.create_role(name="Muted")
        for channel in guild.channels:
            await channel.set_permissions(muted_role, send_messages=False, speak=False)
    if muted_role in member.roles:
        await ctx.send(f"{member.mention} уже замучен!")
        return
    await member.add_roles(muted_role, reason=reason)
    embed = discord.Embed(title="🔇 Мут", description=f"{member.mention} замучен.\n**Причина:** {reason}", color=discord.Color.greyple())
    await ctx.send(embed=embed)

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: str, *, reason="Не указана"):
    guild = ctx.guild
    try:
        user_id = int(user_id)
        user = await bot.fetch_user(user_id)
        await guild.unban(user, reason=reason)
        embed = discord.Embed(title="🔓 Разбан", description=f"{user.mention} разбанен.\n**Причина:** {reason}", color=discord.Color.green())
        await ctx.send(embed=embed)
    except ValueError:
        await ctx.send("ID должен быть числом!")
    except discord.NotFound:
        await ctx.send("Пользователь не найден в банах!")

@bot.command(name="unmute")
@commands.has_permissions(manage_roles=True)
async def unmute(ctx, member: discord.Member, *, reason="Не указана"):
    guild = ctx.guild
    muted_role = discord.utils.get(guild.roles, name="Muted")
    if not muted_role or muted_role not in member.roles:
        await ctx.send(f"{member.mention} не замучен!")
        return
    await member.remove_roles(muted_role, reason=reason)
    embed = discord.Embed(title="🔊 Размут", description=f"{member.mention} размучен.\n**Причина:** {reason}", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="warn")
@commands.has_permissions(manage_roles=True)
async def warn(ctx, member: discord.Member, *, reason="Не указана"):
    user_id = str(member.id)
    warnings = db.child("warnings").child(user_id).get().val()
    
    if isinstance(warnings, int):
        warnings = [{"reason": "Неизвестно", "timestamp": "До обновления"}] * warnings
    elif warnings is None:
        warnings = []
    else:
        warnings = list(warnings.values()) if isinstance(warnings, dict) else warnings
    
    new_warning = {"reason": reason, "timestamp": discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
    warnings.append(new_warning)
    warn_count = len(warnings)
    
    db.child("warnings").child(user_id).set(warnings)
    
    embed = discord.Embed(
        title="⚠️ Предупреждение",
        description=f"{member.mention} получил варн.\n**Причина:** {reason}\n**Время:** {new_warning['timestamp']}\n**Всего:** {warn_count}",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)
    
    if warn_count >= 3:
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False)
        await member.add_roles(muted_role)
        embed = discord.Embed(title="🔇 Мут", description=f"{member.mention} замучен за 3 варна!", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name="r34")
async def r34(ctx, *, query: str):
    """Получить случайное изображение с Rule34.xxx по запросу."""
    # Проверка, является ли канал NSFW
    if not ctx.channel.is_nsfw():
        embed = discord.Embed(
            title="❌ Ошибка",
            description="Эта команда доступна только в NSFW-каналах!",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    # URL API Rule34.xxx
    api_url = "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index"
    params = {
        "tags": query.replace(" ", "+"),  # Заменяем пробелы на + для URL
        "limit": 100,                    # Ограничение на количество результатов
        "json": 1                        # Формат JSON
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, params=params) as response:
            if response.status != 200:
                embed = discord.Embed(
                    title="❌ Ошибка",
                    description="Не удалось получить данные с Rule34.xxx!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            data = await response.json()
            if not data or len(data) == 0:
                embed = discord.Embed(
                    title="❌ Ничего не найдено",
                    description=f"По запросу '{query}' ничего не найдено!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return

            # Выбираем случайное изображение
            post = random.choice(data)
            image_url = post.get("file_url")

            # Создаём Embed с изображением
            embed = discord.Embed(
                title=f"Rule34.xxx: {query}",
                description=f"Источник: [Rule34.xxx](https://rule34.xxx/index.php?page=post&s=view&id={post['id']})",
                color=discord.Color.purple()
            )
            embed.set_image(url=image_url)
            embed.set_footer(text=f"Запрошено {ctx.author.name}")

            await ctx.send(embed=embed)

@bot.command(name="unwarn")
@commands.has_permissions(manage_roles=True)
async def unwarn(ctx, member: discord.Member, option: str = "one"):
    user_id = str(member.id)
    warnings = db.child("warnings").child(user_id).get().val()
    
    if warnings is None or (isinstance(warnings, list) and not warnings):
        await ctx.send(f"{member.mention} не имеет варнов!")
        return
    
    if isinstance(warnings, int):
        warnings = [{"reason": "Неизвестно", "timestamp": "До обновления"}] * warnings
    
    warnings = list(warnings.values()) if isinstance(warnings, dict) else warnings
    
    if option.lower() == "all":
        db.child("warnings").child(user_id).remove()
        embed = discord.Embed(title="🗑️ Удаление варнов", description=f"Все варны {member.mention} удалены!", color=discord.Color.green())
    else:
        warnings.pop()
        if warnings:
            db.child("warnings").child(user_id).set(warnings)
        else:
            db.child("warnings").child(user_id).remove()
        embed = discord.Embed(title="🗑️ Удаление варна", description=f"Удалён последний варн {member.mention}.\nОсталось: {len(warnings)}", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command(name="warns")
async def warns(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)
    warnings = db.child("warnings").child(user_id).get().val()
    
    if warnings is None or (isinstance(warnings, list) and not warnings):
        embed = discord.Embed(title="📜 Варны", description=f"{member.mention} не имеет варнов.", color=discord.Color.green())
        await ctx.send(embed=embed)
        return
    
    if isinstance(warnings, int):
        warnings = [{"reason": "Неизвестно", "timestamp": "До обновления"}] * warnings
    
    warnings = list(warnings.values()) if isinstance(warnings, dict) else warnings
    
    embed = discord.Embed(title=f"📜 Варны {member.name}", color=discord.Color.orange())
    for i, warn in enumerate(warnings, 1):
        embed.add_field(name=f"#{i}", value=f"Причина: {warn['reason']}\nВремя: {warn['timestamp']}", inline=False)
    embed.set_footer(text=f"Всего: {len(warnings)}")
    await ctx.send(embed=embed)

@bot.command(name="serverinfo")
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"ℹ️ {guild.name}", color=discord.Color.purple())
    embed.add_field(name="ID", value=guild.id, inline=True)
    embed.add_field(name="Владелец", value=guild.owner.mention, inline=True)
    embed.add_field(name="Создан", value=guild.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=True)
    embed.add_field(name="Участников", value=guild.member_count, inline=True)
    embed.add_field(name="Ролей", value=len(guild.roles), inline=True)
    embed.add_field(name="Каналов", value=len(guild.channels), inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="🏓 Пинг", description=f"Задержка: {latency} мс", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="info")
async def info(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"ℹ️ {member.name}", color=discord.Color.purple())
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(name="Присоединился", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Роли", value=", ".join([role.name for role in member.roles[1:]]), inline=False)
    embed.set_thumbnail(url=member.avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="clear")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount <= 0:
        await ctx.send("Количество должно быть больше 0!")
        return
    if amount > 100:
        await ctx.send("Максимум 100 сообщений!")
        return
    await ctx.channel.purge(limit=amount + 1)
    embed = discord.Embed(title="🧹 Очистка", description=f"Удалено {amount} сообщений.", color=discord.Color.green())
    await ctx.send(embed=embed, delete_after=5)

@bot.command(name="roll")
async def roll(ctx, range: str = "1-6"):
    try:
        start, end = map(int, range.split("-"))
        if start >= end:
            await ctx.send("Начало должно быть меньше конца!")
            return
        result = random.randint(start, end)
        embed = discord.Embed(title="🎲 Кубик", description=f"Результат: {result}", color=discord.Color.orange())
        await ctx.send(embed=embed)
    except ValueError:
        await ctx.send("Формат: '1-6'!")

@bot.command(name="say")
async def say(ctx, *, message):
    await ctx.send(message)

@bot.command(name="coin")
async def coin(ctx):
    result = random.choice(["Орёл", "Решка"])
    embed = discord.Embed(title="🪙 Монетка", description=f"Результат: **{result}**", color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.command(name="uptime")
async def uptime(ctx):
    uptime_seconds = int(time.time() - start_time)
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    embed = discord.Embed(title="⏳ Uptime", description=f"Бот работает: {uptime_str}", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="remind")
async def remind(ctx, duration: str, *, reminder: str):
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        unit = duration[-1].lower()
        amount = int(duration[:-1])
        if unit not in time_units:
            raise ValueError
        seconds = amount * time_units[unit]
        await ctx.send(f"Напоминание на {duration}: {reminder}")
        await asyncio.sleep(seconds)
        embed = discord.Embed(title="⏰ Напоминание", description=f"{ctx.author.mention}, ты просил: {reminder}", color=discord.Color.green())
        await ctx.send(embed=embed)
    except (ValueError, IndexError):
        await ctx.send("Формат: '10s', '5m', '2h', '1d'!")

@bot.command(name="8ball")
async def eightball(ctx, *, question: str):
    answers = ["Да", "Нет", "Может быть", "Скорее всего", "Не уверен", "Спроси позже", "Точно нет", "Определённо да"]
    response = random.choice(answers)
    embed = discord.Embed(title="🎱 Шар", description=f"Вопрос: {question}\nОтвет: {response}", color=discord.Color.purple())
    await ctx.send(embed=embed)

@bot.command(name="quote")
async def quote(ctx):
    quotes = [
        "Жизнь — это то, что происходит, пока ты строишь планы. — Джон Леннон",
        "Не важно, как медленно ты идёшь, главное — не останавливаться. — Конфуций",
        "Squad #43 — это не просто число, это стиль жизни. — @aukeu",
    ]
    quote = random.choice(quotes)
    embed = discord.Embed(title="📜 Цитата", description=quote, color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.command(name="roast")
async def roast(ctx, member: discord.Member):
    roasts = [
        f"{member.mention}, ты так медленно соображаешь, что улитки тебя обгоняют.",
        f"{member.mention}, твоя аватарка выглядит как ошибка природы.",
        f"{member.mention}, ты настолько не в теме, что даже Wi-Fi тебя не ловит.",
    ]
    roast = random.choice(roasts)
    embed = discord.Embed(title="🔥 Roast", description=roast, color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command(name="leaderboard")
async def leaderboard(ctx, criterion: str = "warns"):
    if criterion.lower() != "warns":
        await ctx.send("Пока доступен только топ по варнам (43 leaderboard warns)!")
        return
    
    all_warnings = db.child("warnings").get().val() or {}
    leaderboard = []
    for user_id, warnings in all_warnings.items():
        warn_count = len(warnings) if isinstance(warnings, (list, dict)) else warnings
        leaderboard.append((user_id, warn_count))
    
    leaderboard.sort(key=lambda x: x[1], reverse=True)
    top_5 = leaderboard[:5]
    
    embed = discord.Embed(title="🏆 Топ по варнам", color=discord.Color.gold())
    for i, (user_id, count) in enumerate(top_5, 1):
        user = await bot.fetch_user(int(user_id))
        embed.add_field(name=f"#{i} {user.name}", value=f"Варнов: {count}", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="shoutout")
async def shoutout(ctx, member: discord.Member, *, message: str):
    embed = discord.Embed(
        title="🌟 Shoutout!",
        description=f"{ctx.author.mention} благодарит {member.mention}!\n**Сообщение:** {message}",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.avatar.url)
    await ctx.send(embed=embed)

@bot.command(name="weather")
async def weather(ctx, *, city: str):
    if not OPENWEATHER_API_KEY:
        await ctx.send("API ключ для погоды не настроен!")
        return
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=ru"
    response = requests.get(url)
    if response.status_code != 200:
        await ctx.send("Не удалось найти город!")
        return
    data = response.json()
    temp = data["main"]["temp"]
    description = data["weather"][0]["description"]
    embed = discord.Embed(title=f"☁️ Погода в {city}", description=f"Температура: {temp}°C\n{description.capitalize()}", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="translate")
async def translate(ctx, lang: str, *, text: str):
    translator = googletrans.Translator()
    try:
        result = await asyncio.to_thread(translator.translate, text, dest=lang)
        embed = discord.Embed(title="🌐 Перевод", description=f"Оригинал: {text}\nПеревод ({lang}): {result.text}", color=discord.Color.purple())
        await ctx.send(embed=embed)
    except ValueError:
        await ctx.send("Неверный код языка! Пример: 'ru', 'en'.")
    except Exception as e:
        await ctx.send(f"Ошибка перевода: {str(e)}")

@bot.command(name="search")
async def search(ctx, *, query: str):
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        await ctx.send("API ключ для поиска не настроен!")
        return
    service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
    try:
        result = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=1).execute()
        if "items" not in result:
            await ctx.send("Ничего не найдено!")
            return
        item = result["items"][0]
        embed = discord.Embed(title="🔍 Поиск", description=f"[{item['title']}]({item['link']})\n{item['snippet']}", color=discord.Color.orange())
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Ошибка поиска: {str(e)}")

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5, speed=1.0):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title', 'Неизвестный трек')
        self.url = data.get('url', 'Неизвестный URL')
        self.speed = speed
        self.duration = data.get('duration', 0)

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, speed=1.0, volume=0.5):
        loop = loop or asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
            if 'entries' in data:
                data = data['entries'][0]
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': f'-vn -filter:a "atempo={speed}"'
            }
            return cls(discord.FFmpegPCMAudio(filename, executable=FFMPEG_PATH, **ffmpeg_options), data=data, speed=speed, volume=volume)
        except youtube_dl.DownloadError as e:
            raise Exception(f"Ошибка загрузки трека: {str(e)}")
        except Exception as e:
            raise Exception(f"Ошибка при обработке аудио: {str(e)}")

async def play_next(ctx):
    guild_id = ctx.guild.id
    if guild_id not in music_queues:
        return

    voice_client = ctx.voice_client
    if not voice_client or not voice_client.is_connected():
        music_queues.pop(guild_id, None)
        looping.pop(guild_id, None)
        return

    queue = music_queues[guild_id].get('queue', deque())
    
    try:
        if looping.get(guild_id, False) and 'current' in music_queues[guild_id]:
            player = await YTDLSource.from_url(
                music_queues[guild_id]['current']['url'],
                loop=bot.loop,
                stream=True,
                speed=music_queues[guild_id].get('speed', 1.0),
                volume=music_queues[guild_id].get('volume', 0.5)
            )
            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
            embed = discord.Embed(title="🔄 Зациклено", description=f"Повтор: {player.title}", color=discord.Color.blue())
            await ctx.send(embed=embed)
        elif queue:
            next_track = queue.popleft()
            player = await YTDLSource.from_url(
                next_track['url'],
                loop=bot.loop,
                stream=True,
                speed=music_queues[guild_id].get('speed', 1.0),
                volume=music_queues[guild_id].get('volume', 0.5)
            )
            music_queues[guild_id]['current'] = {'url': next_track['url'], 'title': player.title, 'duration': player.duration}
            voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
            embed = discord.Embed(title="🎵 Музыка", description=f"Играет: {player.title}", color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            voice_client.stop()
            music_queues.pop(guild_id, None)
            looping.pop(guild_id, None)
            await voice_client.disconnect()
            embed = discord.Embed(title="⏹ Очередь завершена", description="Воспроизведение завершено, бот отключён.", color=discord.Color.red())
            await ctx.send(embed=embed)
    except Exception as e:
        logger.error(f"Ошибка в play_next: {str(e)}")
        embed = discord.Embed(title="❌ Ошибка", description=f"Произошла ошибка при воспроизведении: {str(e)}", color=discord.Color.red())
        await ctx.send(embed=embed)
        voice_client.stop()
        await voice_client.disconnect()
        music_queues.pop(guild_id, None)
        looping.pop(guild_id, None)

@bot.command(name="play")
async def play(ctx, *, url: str):
    if not ctx.author.voice:
        await ctx.send("Ты не в голосовом канале!")
        return
    
    voice_channel = ctx.author.voice.channel
    if not ctx.voice_client:
        try:
            await voice_channel.connect()
        except Exception as e:
            await ctx.send(f"Не удалось подключиться к голосовому каналу: {str(e)}")
            return
    
    voice_client = ctx.voice_client
    guild_id = ctx.guild.id
    
    if guild_id not in music_queues:
        music_queues[guild_id] = {
            'speed': 1.0,
            'volume': 0.5,
            'queue': deque()
        }
    
    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(
                url,
                loop=bot.loop,
                stream=True,
                speed=music_queues[guild_id]['speed'],
                volume=music_queues[guild_id]['volume']
            )
            music_queues[guild_id]['current'] = {'url': url, 'title': player.title, 'duration': player.duration}
            if voice_client.is_playing() or voice_client.is_paused():
                music_queues[guild_id]['queue'].append({'url': url, 'title': player.title})
                embed = discord.Embed(title="➕ Добавлено в очередь", description=f"Трек: {player.title}", color=discord.Color.green())
            else:
                voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
                embed = discord.Embed(title="🎵 Музыка", description=f"Играет: {player.title}", color=discord.Color.blue())
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Не удалось воспроизвести: {str(e)}")

@bot.command(name="queue")
async def queue(ctx, *, url: str):
    if not ctx.author.voice:
        await ctx.send("Ты не в голосовом канале!")
        return
    guild_id = ctx.guild.id
    if guild_id not in music_queues:
        music_queues[guild_id] = {
            'speed': 1.0,
            'volume': 0.5,
            'queue': deque()
        }
    
    async with ctx.typing():
        try:
            data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            if 'entries' in data:
                data = data['entries'][0]
            title = data.get('title')
            music_queues[guild_id]['queue'].append({'url': url, 'title': title})
            embed = discord.Embed(title="➕ Добавлено в очередь", description=f"Трек: {title}\nОчередь: {len(music_queues[guild_id]['queue'])}", color=discord.Color.green())
            await ctx.send(embed=embed)
            
            if not ctx.voice_client:
                await ctx.author.voice.channel.connect()
            voice_client = ctx.voice_client
            if not voice_client.is_playing() and not voice_client.is_paused():
                await play_next(ctx)
        except Exception as e:
            await ctx.send(f"Не удалось добавить в очередь: {str(e)}")

@bot.command(name="clearqueue")
async def clearqueue(ctx):
    guild_id = ctx.guild.id
    if guild_id not in music_queues or not music_queues[guild_id]['queue']:
        await ctx.send("Очередь пуста!")
        return
    
    music_queues[guild_id]['queue'].clear()
    embed = discord.Embed(title="🗑️ Очередь очищена", description="Все треки из очереди удалены.", color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command(name="viewqueue")
async def viewqueue(ctx):
    guild_id = ctx.guild.id
    if guild_id not in music_queues or not music_queues[guild_id]['queue']:
        await ctx.send("Очередь пуста!")
        return
    
    queue = music_queues[guild_id]['queue']
    embed = discord.Embed(title="📜 Очередь воспроизведения", color=discord.Color.blue())
    for i, track in enumerate(queue, 1):
        embed.add_field(name=f"#{i}", value=track['title'], inline=False)
    embed.set_footer(text=f"Всего: {len(queue)}")
    await ctx.send(embed=embed)

@bot.command(name="remove")
async def remove(ctx, index: int):
    guild_id = ctx.guild.id
    if guild_id not in music_queues or not music_queues[guild_id]['queue']:
        await ctx.send("Очередь пуста!")
        return
    
    queue = music_queues[guild_id]['queue']
    if index < 1 or index > len(queue):
        await ctx.send(f"Укажи номер от 1 до {len(queue)}!")
        return
    
    removed_track = queue[index - 1]
    del queue[index - 1]
    embed = discord.Embed(title="🗑️ Удалено из очереди", description=f"Удалён трек: {removed_track['title']}", color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command(name="skip")
async def skip(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("Сейчас ничего не играет!")
        return
    
    guild_id = ctx.guild.id
    voice_client = ctx.voice_client
    voice_client.stop()
    embed = discord.Embed(title="⏭ Пропущено", description="Трек пропущен.", color=discord.Color.blue())
    await ctx.send(embed=embed)
    await play_next(ctx)

@bot.command(name="volume")
async def volume(ctx, volume: int):
    if not ctx.voice_client:
        await ctx.send("Я не в голосовом канале!")
        return
    
    if volume < 0 or volume > 100:
        await ctx.send("Громкость должна быть от 0 до 100!")
        return
    
    guild_id = ctx.guild.id
    music_queues[guild_id]['volume'] = volume / 100
    if ctx.voice_client.source:
        ctx.voice_client.source.volume = volume / 100
    embed = discord.Embed(title="🔊 Громкость", description=f"Установлена громкость: {volume}%", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="nowplaying")
async def nowplaying(ctx):
    guild_id = ctx.guild.id
    if guild_id not in music_queues or 'current' not in music_queues[guild_id]:
        await ctx.send("Сейчас ничего не играет!")
        return
    
    current = music_queues[guild_id]['current']
    duration = f"{int(current['duration'] // 60)}:{int(current['duration'] % 60):02d}" if current['duration'] else "Неизвестно"
    embed = discord.Embed(title="🎶 Сейчас играет", color=discord.Color.blue())
    embed.add_field(name="Название", value=current['title'], inline=False)
    embed.add_field(name="URL", value=current['url'], inline=False)
    embed.add_field(name="Длительность", value=duration, inline=True)
    embed.add_field(name="Очередь", value=len(music_queues[guild_id]['queue']), inline=True)
    await ctx.send(embed=embed)

@bot.command(name="playlist")
async def playlist(ctx, *, url: str):
    if not ctx.author.voice:
        await ctx.send("Ты не в голосовом канале!")
        return
    voice_channel = ctx.author.voice.channel
    if not ctx.voice_client:
        await voice_channel.connect()
    voice_client = ctx.voice_client
    
    guild_id = ctx.guild.id
    if guild_id not in music_queues:
        music_queues[guild_id] = {
            'speed': 1.0,
            'volume': 0.5,
            'queue': deque()
        }
    
    async with ctx.typing():
        try:
            data = await bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            if 'entries' not in data:
                await ctx.send("Это не плейлист!")
                return
            
            tracks = data['entries']
            for track in tracks:
                music_queues[guild_id]['queue'].append({'url': track['url'], 'title': track['title']})
            
            embed = discord.Embed(title="📜 Плейлист добавлен", description=f"Добавлено {len(tracks)} треков в очередь.", color=discord.Color.green())
            await ctx.send(embed=embed)
            
            if not voice_client.is_playing() and not voice_client.is_paused():
                await play_next(ctx)
        except Exception as e:
            await ctx.send(f"Не удалось загрузить плейлист: {str(e)}")

@bot.command(name="shuffle")
async def shuffle(ctx):
    guild_id = ctx.guild.id
    if guild_id not in music_queues or not music_queues[guild_id]['queue']:
        await ctx.send("Очередь пуста!")
        return
    
    queue = list(music_queues[guild_id]['queue'])
    random.shuffle(queue)
    music_queues[guild_id]['queue'] = deque(queue)
    embed = discord.Embed(title="🔀 Перемешано", description="Очередь треков перемешана.", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="loop")
async def loop(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("Сейчас ничего не играет!")
        return
    
    guild_id = ctx.guild.id
    looping[guild_id] = not looping.get(guild_id, False)
    status = "включено" if looping[guild_id] else "выключено"
    embed = discord.Embed(title="🔄 Зацикливание", description=f"Зацикливание {status}", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="speed")
async def speed(ctx, speed: float):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("Сейчас ничего не играет!")
        return
    
    if speed < 0.5 or speed > 2.0:
        await ctx.send("Скорость должна быть от 0.5 до 2.0!")
        return
    
    guild_id = ctx.guild.id
    voice_client = ctx.voice_client
    current = music_queues.get(guild_id, {}).get('current')
    
    if not current:
        await ctx.send("Нет текущего трека!")
        return
    
    voice_client.stop()
    music_queues[guild_id]['speed'] = speed
    player = await YTDLSource.from_url(
        current['url'],
        loop=bot.loop,
        stream=True,
        speed=speed,
        volume=music_queues[guild_id]['volume']
    )
    voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    embed = discord.Embed(title="⏩ Скорость", description=f"Установлена скорость: {speed}x", color=discord.Color.blue())
    await ctx.send(embed=embed)

@bot.command(name="stop")
async def stop(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_connected():
        await ctx.send("Я не в голосовом канале!")
        return
    
    guild_id = ctx.guild.id
    voice_client = ctx.voice_client
    voice_client.stop()
    music_queues.pop(guild_id, None)
    looping.pop(guild_id, None)
    await voice_client.disconnect()
    embed = discord.Embed(title="⏹ Остановлено", description="Музыка остановлена, бот отключён.", color=discord.Color.red())
    await ctx.send(embed=embed)

@bot.command(name="pause")
async def pause(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("Сейчас ничего не играет!")
        return
    
    ctx.voice_client.pause()
    embed = discord.Embed(title="⏸ На паузе", description="Музыка приостановлена.", color=discord.Color.orange())
    await ctx.send(embed=embed)

@bot.command(name="compliment")
async def compliment(ctx, member: discord.Member = None):
    """Отправляет комплимент участнику."""
    member = member or ctx.author
    compliments = [
        f"{member.mention}, ты просто огонь! 🔥",
        f"{member.mention}, твоя энергия заряжает всех вокруг! ⚡",
        f"{member.mention}, ты делаешь Squad #43 лучше каждый день! 🌟",
        f"{member.mention}, твой юмор — это что-то невероятное! 😂",
        f"{member.mention}, ты — настоящая душа сообщества! ❤️",
    ]

    compliment = random.choice(compliments)
    embed = discord.Embed(
        title="💖 Комплимент",
        description=compliment,
        color=discord.Color.pink()
    )
    embed.set_thumbnail(url=member.avatar.url)
    await ctx.send(embed=embed)
    logger.info(f"Комплимент отправлен {ctx.author.id} для {member.id}")

import aiohttp

@bot.command(name="meme")
async def meme(ctx, template: str, top_text: str, bottom_text: str):
    """Создаёт мем с заданным текстом."""
    # Популярные шаблоны (можно расширить)
    templates = {
        "drake": "Drake Hotline Bling",
        "distracted": "Distracted Boyfriend",
        "spongebob": "Spongebob Mocking",
        "success": "Success Kid",
    }

    template_name = template.lower()
    if template_name not in templates:
        await ctx.send(f"Доступные шаблоны: {', '.join(templates.keys())}")
        return

    # Используем API Meme Generator (замените API_KEY на ваш ключ)
    MEME_API_URL = "https://api.memegen.link/images"
    url = f"{MEME_API_URL}/{template_name}/{top_text}/{bottom_text}.png"

    embed = discord.Embed(
        title="😂 Ваш мем готов!",
        description=f"Создан мем от {ctx.author.mention}",
        color=discord.Color.purple()
    )
    embed.set_image(url=url)
    await ctx.send(embed=embed)
    logger.info(f"Мем создан {ctx.author.id}, шаблон: {template_name}, текст: {top_text}/{bottom_text}")

@bot.command(name="giveaway")
@commands.has_permissions(administrator=True)  # Только для администраторов
async def giveaway(ctx, duration: str, *, prize: str):
    """Создаёт розыгрыш с призом."""
    time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    try:
        unit = duration[-1].lower()
        amount = int(duration[:-1])
        if unit not in time_units:
            raise ValueError
        seconds = amount * time_units[unit]
    except (ValueError, IndexError):
        await ctx.send("Формат времени: '10s', '5m', '2h', '1d'!")
        return

    embed = discord.Embed(
        title="🎉 Розыгрыш!",
        description=f"**Приз:** {prize}\n**Время:** {duration}\nРеагируй с 🎉, чтобы участвовать!",
        color=discord.Color.gold()
    )
    embed.set_footer(text="Squad #43 | Удачи!")
    msg = await ctx.send("@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))
    await msg.add_reaction("🎉")

    await asyncio.sleep(seconds)

    # Проверка участников
    msg = await ctx.channel.fetch_message(msg.id)
    participants = set()
    for reaction in msg.reactions:
        if reaction.emoji == "🎉":
            async for user in reaction.users():
                if user != bot.user:
                    participants.add(user)

    if not participants:
        await ctx.send("Никто не участвовал в розыгрыше! 😢")
        return

    winner = random.choice(list(participants))
    embed = discord.Embed(
        title="🏆 Победитель розыгрыша!",
        description=f"**Приз:** {prize}\n**Победитель:** {winner.mention}\nПоздравляем!",
        color=discord.Color.green()
    )
    await ctx.send("@everyone", embed=embed, allowed_mentions=discord.AllowedMentions(everyone=True))
    logger.info(f"Розыгрыш завершён. Приз: {prize}, Победитель: {winner.id}")

@bot.command(name="resume")
async def resume(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_paused():
        await ctx.send("Музыка не на паузе!")
        return
    
    ctx.voice_client.resume()
    embed = discord.Embed(title="▶️ Возобновлено", description="Музыка снова играет.", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Недостаточно прав!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Пропущен аргумент!")
    else:
        logger.error(f"Ошибка: {error}")
        await ctx.send(f"Произошла ошибка: {str(error)}")

async def shutdown_handler():
    logger.info("Бот завершает работу...")
    await send_disconnect_message()
    await bot.close()

def signal_handler(signum, frame):
    asyncio.create_task(shutdown_handler())

if __name__ == "__main__":
    if not TOKEN:
        print("Ошибка: Токен бота не найден!")
        exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(bot.start(TOKEN))
    except KeyboardInterrupt:
        loop.run_until_complete(shutdown_handler())
    finally:
        loop.close()
