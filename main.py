from os import getenv
from dotenv import load_dotenv
import discord
from discord.ext import commands
from pymongo import MongoClient
from db import get_leaderboard, submit_time
import asyncio


load_dotenv()

from twitch import twitch_listener

TEST_ONLY = True

TOKEN = getenv('TOKEN')

intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="!", intents=intents)

user_ids = {}


@client.event
async def on_ready():
    print(f"Connected as {client.user}")

    client.TEST_CHANNEL = await client.fetch_channel(getenv('TEST_CHANNEL_ID'))
    client. MAIN_CHANNEL = client.TEST_CHANNEL if TEST_ONLY else await client.fetch_channel(getenv('MAIN_CHANNEL_ID'))
    client.LEADERBOARD_CHANNEL = client.TEST_CHANNEL if TEST_ONLY else await client.fetch_channel(getenv('LEADERBOARD_CHANNEL_ID'))
    client.LIVE_CHANNEL = client.TEST_CHANNEL if TEST_ONLY else await client.fetch_channel(getenv('GOLIVE_CHANNEL_ID'))

    channel = client.MAIN_CHANNEL

    if channel is None:
        print("Channel not found!")
        return

    asyncio.create_task(twitch_listener(sendLiveNotification))

    #await channel.send("Hello from my Python bot!")

    # async for message in channel.history(limit=100):
    #     print(message.author, message.content)
    #     if message.author.id not in user_ids:
    #         user_ids[message.author.id] = str(message.author)

    # with open("USERS.txt", "w") as f:
    #     for key, value in user_ids.items():
    #         f.write(f"{key}: {value}\n")



@client.event
async def on_message(message):
    print(message.author, ':', message.content)

    await client.process_commands(message)


def sec_to_time(secs):
    hours = secs // 3600
    secs -= hours * 3600
    
    mins = secs // 60
    secs -= mins * 60


    return f'{str(hours) + ':' if hours > 0 else ''}{mins if mins >= 10 else '0' + str(mins)}:{secs if secs >= 10 else '0' + str(secs)}'


def time_to_sec(time_str):
    parts = list(map(int, time_str.split(":")))
    seconds = 0

    for part in parts:
        seconds = seconds * 60 + part

    return seconds



USER_IDS = {
    '477950249596354582': 'Nation',
    '1324735698300833793': 'Walker',
    '330421550534885386': 'Ape',
    '706712798696308817': 'Toni',
    '664950169132859453': 'Tank',
    '258713391093252106': 'Yard'
}

def map_user_id(userObj):
    id = userObj.id
    if id in USER_IDS:
        return USER_IDS[id]

    else: 
        return userObj.display_name

cats = ['16 Star', '70 Star', '1 Star']

leaderboards = {'16 Star': get_leaderboard('16 Star'), '70 Star': get_leaderboard('70 Star'), '1 Star': get_leaderboard('1 Star')}

for cat in cats:
    leaderboards[cat] = get_leaderboard(cat)



async def newTimeSubmission(user_id, username, seconds, category):

    submit_time(category, user_id, username, seconds, sec_to_time(seconds))

    channel = client.LEADERBOARD_CHANNEL
    await channel.send(f'{username} just submitted a new **{category}** time of `{sec_to_time(seconds)}`')
    await send_leaderboard(channel, cats.index(category), username)



class SubmissionModal(discord.ui.Modal, title="Submit a new time"):

    time = discord.ui.TextInput(
        label=f"Completion Time",
        placeholder="1:32:24",
        required=True,
        max_length=12
    )

    async def on_submit(self, interaction: discord.Interaction):
        time_str = self.time.value.strip()

        try:
            seconds = time_to_sec(time_str)
        except ValueError:
            await interaction.response.send_message(
                "Invalid time format. Use HH:MM:SS or MM:SS.",
                ephemeral=True
            )
            return

        user_id = str(interaction.user.id)
        username = USER_IDS[user_id] if user_id in USER_IDS else interaction.user.display_name

        # Get the currently selected leaderboard
        category = self.category
        scores = leaderboards[category]

        # Add submission
        scores.append({'User': user_id, 'DisplayName': username, 'Time': seconds, 'DisplayTime': sec_to_time(seconds)})

        # Sort by fastest time
        scores.sort(key=lambda entry: entry['Time'])

        print(scores)

        await interaction.response.send_message(
            f"Time submitted for **{category}**: `{time_str}`",
            ephemeral=True
        )

        await newTimeSubmission(user_id, username, seconds, category)

    def __init__(self, category):
        super().__init__()
        self.category = category


class LeaderboardView(discord.ui.View):

    def __init__(self, current=0, recentUsername=None):
        super().__init__(timeout=None)
        self.current = current
        self.newSubCat = current
        self.categories = list(leaderboards.keys())
        self.recentUserName = recentUsername

    def create_embed(self):

        category = self.categories[self.current]
        scores = get_leaderboard(category)
        scores.sort(key=lambda entry: entry['Time'])

        description = ""

        for i in range(len(scores)):
            description += f"{'### ' if scores[i]['DisplayName'] == self.recentUserName and self.current == self.newSubCat else ''}**{i+1}.** {scores[i]['DisplayName']} — `{scores[i]['DisplayTime']}`\n"


        embed = discord.Embed(
            title=f"{category} Leaderboard",
            description=description,
            color=discord.Color.blue()
        )

        embed.set_footer(text=f"<- {self.categories[(self.current-1) % len(self.categories)]}\t{self.categories[(self.current+1) % len(self.categories)]} ->")

        return embed

    async def update(self, interaction):
        await interaction.response.edit_message(
            embed=self.create_embed(),
            view=self
        )



    @discord.ui.button(label='Previous', style=discord.ButtonStyle.secondary)
    async def previous(self, interaction, button):
        self.current = (self.current - 1) % len(self.categories)
        await self.update(interaction)


    @discord.ui.button(
        label="Submit Time",
        style=discord.ButtonStyle.success
    )
    async def submit(self, interaction, button):
        await interaction.response.send_modal(
            SubmissionModal(self.categories[self.current])
        )

    @discord.ui.button(label='Next', style=discord.ButtonStyle.primary)
    async def next(self, interaction, button):
        self.current = (self.current + 1) % len(self.categories)
        await self.update(interaction)


@client.command()
async def leaderboard(ctx):
    print('leaderboard command')
    view = LeaderboardView()
    await ctx.send(embed=view.create_embed(), view=view)

async def send_leaderboard(channel, catIndex, newUser):
    view = LeaderboardView(catIndex, newUser)
    await channel.send(embed=view.create_embed(), view=view)


async def sendLiveNotification(name, login):
    print(name, login)
    await client.LIVE_CHANNEL.send(
        f"🔴 **{name} is now LIVE!**\n"
        f"https://twitch.tv/{login}"
    )





client.run(TOKEN)