import sqlite3
import asyncio
import discord
from discord.ext import commands
from discord.utils import get

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="$", intents=intents, case_insensitive=True)

new_line = '\n'
bot.remove_command('help')
debug = False
# MUST READ NOTES:
# nation_score, gdp and population have no logic behind them, meaning it's worthless for now
# there is no way to recruit troops
# there are no weapons
# you can't make planes
# you can't make tanks
# you can't make barracks
# you can't make AA
# you can't make artillery
# you can only view infra, not make it
# you can't view info about infra
# there aren't emojis for infra because I am too lazy (deal with it)
# good luck making most of that stuff rev (hehe)


# Basic Error Handler - Just add a new elif if you want to add another error to the list
# If you get the "Unspecified error" error, and you want to check what the issue is through the terminal, either remove
@bot.event
async def on_command_error(ctx, error):
    global debug
    if debug is False:   # Checks if bot is in debug mode
        if hasattr(ctx.command, 'on_error'):
            return
        error = getattr(error, 'original', error)
        if isinstance(error, commands.CommandNotFound, ):
            embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                                  description="Command not found.")
            embed.set_footer(text="Check the help command")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                                  description="An unspecified error has occurred.")
            embed.set_footer(text="Ping a dev so they can look into it")
            await ctx.send(embed=embed)
    else:
        print(error)


def dev_check(usid):
    return usid == 837257162223910912 or usid == 669517694751604738


# Connect to the sqlite DB (it will create a new DB if it doesn't exit)

conn = sqlite3.connect('player_info.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_info(
        user_id INTEGER PRIMARY KEY,
        nation_name TEXT
        )
    ''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_stats(
        name TEXT PRIMARY KEY,
        nation_score INTEGER,
        gdp INTEGER,
        population INTEGER
        )
    ''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_mil(
        name_nation TEXT PRIMARY KEY,
        troops INTEGER,
        planes INTEGER,
        weapon INTEGER,
        tanks INTEGER,
        artillery INTEGER,
        anti_air INTEGER,
        barracks INTEGER
        )
    ''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS infra(
        name TEXT PRIMARY KEY,
        basic_house INTEGER,
        small_flat INTEGER,
        apt_complex INTEGER,
        skyscraper INTEGER,
        lumber_mill INTEGER,
        coal_mine INTEGER,
        iron_mine INTEGER,
        lead_mine INTEGER,
        bauxite_mine INTEGER,
        oil_derrick INTEGER,
        uranium_mine INTEGER,
        farm INTEGER,
        aluminium_factory INTEGER,
        steel_factory INTEGER,
        oil_refinery INTEGER,
        ammo_factory INTEGER,
        concrete_factory INTEGER
        )
    ''')


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")


@bot.command()
async def ping(ctx):
    lat = int(bot.latency * 1000)
    await ctx.send(f'Pong! {lat}ms')


@bot.command()   # Debug mode status
async def debug_status(ctx):
    if dev_check(ctx.author.id):
        global debug
        await ctx.send(f'Debug Status: {debug}')
    else:
        print(f'{ctx.author} attempted to enable debug')
        await ctx.send(f'Permission denied: You are not a developer.')


@bot.command()   # Debug mode switcher
async def debug_mode(ctx):
    if dev_check(ctx.author.id):
        global debug
        if debug:
            debug = False
            await ctx.send(f'Debug mode: OFF')
            print("Debug disabled")
        else:
            debug = True
            await ctx.send(f'Debug mode: ON')
            print("Debug enabled")
    else:
        print(f'{ctx.author} attempted to enable debug')
        await ctx.send(f'Permission denied: You are not a developer.')


# Private Channel Command
@bot.command()
async def private(ctx):
    chname = ctx.author.name

    def kat_chan_id(context, ch_name):  # Finds and gets id of channel
        for channel in context.guild.channels:
            if channel.name == ch_name:
                return channel.id

    if any(chname in channel.name for channel in ctx.guild.channels):  # Checks if channel already exists
        chid = kat_chan_id(ctx, chname)
        embed = discord.Embed(colour=0x8212DF, title="Instance Already Running", type='rich',
                              description=f'Cannot start another instance because an instance for you already exists in <#{str(chid)}>')
        await ctx.send(embed=embed)
    else:  # Creates Private Channel
        topic = chname + '\'s Project Thaw private channel'
        category = bot.get_channel()  # Private channel category DON'T FORGET TO INSERT THE ID OF THE CATEGORY YOU WANT THE PRIVATE CHANNELS TO BE IN
        overwrites = {
            discord.utils.get(ctx.guild.roles, name="Overseer"): discord.PermissionOverwrite(read_messages=True),
            # Overseer / Game Master Role
            ctx.message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            ctx.author: discord.PermissionOverwrite(read_messages=True)
        }
        await ctx.guild.create_text_channel(name=chname, category=category, overwrites=overwrites, topic=topic)
        channel = get(ctx.guild.channels, name=chname)  # Gets channel
        msg = await channel.send(f'<@{ctx.author.id}>')
        await msg.delete()
        await asyncio.sleep(3600)  # Time before channel gets deleted
        await channel.delete()


@bot.command()
async def create(ctx):
    user_id = ctx.author.id

    # Check if the user already has an account
    cursor.execute('SELECT 1 FROM user_info WHERE user_id = ?', (user_id,))
    existing_record = cursor.fetchone()

    if existing_record:
        embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                              description=f'You already created a nation.')
        embed.set_footer(text="Dementia")
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(colour=0xFFF86E, title="Creating Nation", type='rich',
                          description="What is the name of your nation?"
                                      "Name cannot be longer than 25 characters.")
    emb = await ctx.send(embed=embed)

    # Checks if response is made by the same user and in the same channel
    def msgchk(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    try:
        nt_name = await bot.wait_for('message', check=msgchk, timeout=30.0)
    except asyncio.TimeoutError:
        return await ctx.send("You took too long to respond.")
    nat_name = nt_name.content

    if len(nat_name) > 25:
        embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                              description=f'Your nation name cannot be longer than 25 characters.')
        await emb.edit(embed=embed)
        return

    embed = discord.Embed(
        title='Nation Successfully Created',
        description=f'This is the glorious start of the **{nat_name}**! '
                    f'{new_line}We wish you a successful journey in leading your people to greatness.',
        color=0x5BF9A0
    )
    await emb.edit(embed=embed)

    # insert data into the table
    cursor.execute('INSERT INTO user_info (user_id, nation_name) VALUES (?, ?)', (user_id, nat_name))
    conn.commit()

    print(f"Successfully added {user_id}({nat_name})")

    # add base stats to the user
    cursor.execute('INSERT INTO user_stats (name, nation_score, gdp, population) VALUES (?, ?, ?, ?)',
                   (nat_name, 0, 0, 100000))
    conn.commit()

    # add base mil stats to the user
    cursor.execute(
        'INSERT INTO user_mil (name_nation, troops, planes, weapon, tanks, artillery, anti_air, barracks) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (nat_name, 0, 0, 0, 0, 0, 0, 0))
    conn.commit()

    print(f"Successfully added stats to {user_id}({nat_name})")

    # Add base infra stats to the user
    cursor.execute(
        'INSERT INTO infra (name, basic_house, small_flat, apt_complex, skyscraper, lumber_mill, coal_mine, iron_mine, lead_mine, bauxite_mine, oil_derrick, uranium_mine, farm, aluminium_factory, steel_factory, oil_refinery, ammo_factory, concrete_factory) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
        (nat_name, 12500, 1000, 834, 0, 10, 100, 10, 10, 10, 10, 0, 2500, 0, 0, 0, 0,
         0))  # the values came from ice cube's game sheet so just use that as a reference
    conn.commit()

    print(f"Successfully added infra to {user_id}({nat_name})")


@bot.command()
async def rename(ctx, new_name: str):
    if new_name == "":
        embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                              description=f'You forgot to write the new name.{new_line}{new_line}'
                                          f'Command Format: `$rename [new_name]`')
        await ctx.send(embed=embed)

    user_id = ctx.author.id

    if len(new_name) > 25:
        embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                              description=f'Your nation name cannot be longer than 25 characters.')
        await ctx.send(embed=embed)
        return

    cursor.execute('SELECT nation_name FROM user_info WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    nation_name = result[0]

    cursor.execute('SELECT 1 FROM user_info WHERE user_id = ?', (user_id,))
    existing_record = cursor.fetchone()

    if existing_record:
        # updates the user_info table
        cursor.execute('UPDATE user_info SET nation_name = ? WHERE user_id = ?', (new_name, user_id))
        conn.commit()
        # updates the user_stats table
        cursor.execute('UPDATE user_stats SET name = ? WHERE name = ?', (new_name, nation_name))
        conn.commit()
        # updates the user_mil table
        cursor.execute('UPDATE user_mil SET name_nation = ? WHERE name_nation = ?', (new_name, nation_name))
        conn.commit()
        # updates the infra table
        cursor.execute('UPDATE infra SET name = ? WHERE name = ?', (new_name, nation_name))
        conn.commit()

        embed = discord.Embed(
            title='Nation Rename',
            description=f'You have successfully changed your nation\'s name to **{new_name}**!',
            color=0x5BF9A0
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                              description=f'You do not have a nation.{new_line}'
                                          f'To create one, type `$create`.')
        await ctx.send(embed=embed)


@bot.command()
async def stats(ctx):
    user_id = ctx.author.id

    # fetch user nation_name
    cursor.execute('SELECT nation_name FROM user_info WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        nation_name = result[0]

        # fetch user stats
        cursor.execute('SELECT name, nation_score, gdp, population FROM user_stats WHERE name = ?', (nation_name,))
        stats_result = cursor.fetchone()

        if stats_result:
            name, nation_score, gdp, population = stats_result

            embed = discord.Embed(
                title=f"📊 {name}'s Stats",
                description=f'Name: {name}',
                color=0x04a5e5
            )
            embed.add_field(name='🫅 Ruler', value=f"<@{user_id}>", inline=False)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name='🏆 Nation Score', value=f'{nation_score}', inline=False)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name='📈 Gross Domestic Product', value=f'{gdp}', inline=False)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name='👪 Population', value=f'{population}', inline=False)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                                  description=f'Cannot find stats.')
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                              description=f'You do not have a nation.{new_line}'
                                          f'To create one, type `$create`.')
        await ctx.send(embed=embed)


@bot.command()
async def mstats(ctx):
    user_id = ctx.author.id

    # fetch user nation_name
    cursor.execute('SELECT nation_name FROM user_info WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        nation_name = result[0]

        # fetch user's mil stats
        cursor.execute(
            'SELECT name_nation, troops, planes, weapon, tanks, artillery, anti_air, barracks FROM user_mil WHERE name_nation = ?',
            (nation_name,))
        mil_result = cursor.fetchone()

        if mil_result:
            name_nation, troops, planes, weapon, tanks, artillery, anti_air, barracks = mil_result

            embed = discord.Embed(
                title=f"⚔ {name_nation}'s Military Stats",
                description='',
                color=0xe64553
            )
            embed.add_field(name='🪖 Troops', value=f'{troops}', inline=False)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name='⛟ Tanks', value=f'{tanks}', inline=False)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name='💥 Artillery', value=f'{artillery}', inline=False)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name='💥 Anti-Air', value=f'{anti_air}', inline=False)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name='🛫 Planes', value=f'{planes}', inline=False)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name='🎖 Barracks', value=f'{barracks}', inline=False)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name='🔫 Weapon', value=f'{weapon}', inline=False)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                                  description=f'Cannot find stats.')
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                              description=f'You do not have a nation.{new_line}'
                                          f'To create one, type `$create`.')
        await ctx.send(embed=embed)


@bot.command()
async def infra(ctx):
    user_id = ctx.author.id

    # fetch user nation_name
    cursor.execute('SELECT nation_name FROM user_info WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result:
        nation_name = result[0]

        # fetch user's infra
        cursor.execute(
            'SELECT name, basic_house, small_flat, apt_complex, skyscraper, lumber_mill, coal_mine, iron_mine, lead_mine, bauxite_mine, oil_derrick, uranium_mine, farm, aluminium_factory, steel_factory, oil_refinery, ammo_factory, concrete_factory FROM infra WHERE name = ?',
            (nation_name,))
        infra_result = cursor.fetchone()

        if infra_result:
            name, basic_house, small_flat, apt_complex, skyscraper, lumber_mill, coal_mine, iron_mine, lead_mine, bauxite_mine, oil_derrick, uranium_mine, farm, aluminium_factory, steel_factory, oil_refinery, ammo_factory, concrete_factory = infra_result

            fields = [
                ("Housing", f"Displays {name}'s housing infra."),
                ("", ""),
                ("Basic House", str(basic_house)),
                ("", ""),
                ("Small Flat", str(small_flat)),
                ("", ""),
                ("Apartment Complex", str(apt_complex)),
                ("", ""),
                ("Skyscraper", str(skyscraper)),
                ("", ""),
                ("Production", f"Displays {name}'s production infra."),
                ("", ""),
                ("Lumber Mill", str(lumber_mill)),
                ("", ""),
                ("Coal Mine", str(coal_mine)),
                ("", ""),
                ("Iron Mine", str(iron_mine)),
                ("", ""),
                ("Lead Mine", str(lead_mine)),
                ("", ""),
                ("Bauxite Mine", str(bauxite_mine)),
                ("", ""),
                ("Oil Derrick", str(oil_derrick)),
                ("", ""),
                ("Uranium Mine", str(uranium_mine)),
                ("", ""),
                ("Farm", str(farm)),
                ("", ""),
                ("Aluminium Factory", str(aluminium_factory)),
                ("", ""),
                ("Steel Factory", str(steel_factory)),
                ("", ""),
                ("Oil Refinery", str(oil_refinery)),
                ("", ""),
                ("Munitions Factory", str(ammo_factory)),
                ("", ""),
                ("Concrete Factory", str(concrete_factory)),
            ]

            # paginate (if that's a word) the fields
            pages = []
            current_page = 0
            fields_per_page = 10

            while current_page < len(fields):
                embed = discord.Embed(title=f"{name}'s Infrastructure", color=0x8839ef)

                for field_name, field_value in fields[current_page:current_page + fields_per_page]:
                    embed.add_field(name=field_name, value=field_value, inline=False)

                pages.append(embed)
                current_page += fields_per_page

            # Send the first page and add reactions for navigation
            message = await ctx.send(embed=pages[0])
            await message.add_reaction('⬅️')
            await message.add_reaction('➡️')

            def check(react, usr):
                return usr == ctx.author and str(react.emoji) in ['⬅️', '➡️']

            current_page = 0

            while True:
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
                except TimeoutError:
                    break

                if str(reaction.emoji) == '➡️' and current_page + 1 < len(pages):
                    current_page += 1
                elif str(reaction.emoji) == '⬅️' and current_page > 0:
                    current_page -= 1

                await message.edit(embed=pages[current_page])
                await message.remove_reaction(reaction.emoji, user)
        else:
            embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                                  description=f'Cannot find stats.')
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed(colour=0xEF2F73, title="Error", type='rich',
                              description=f'You do not have a nation.{new_line}'
                                          f'To create one, type `$create`.')
        await ctx.send(embed=embed)


# Help Command
@bot.command()
async def help(ctx, cmd: str = ""):
    cmd = cmd.lower()

    match cmd:   # Description and syntax of each command
        case "create":
            embed = discord.Embed(colour=0xdd7878, title="Help: Create", type='rich',
                                  description=f'Syntax: `$create`{new_line}{new_line}'
                                              f'Creates a new nation if you don\'t have one already')
            await ctx.send(embed=embed)
        case "private":
            embed = discord.Embed(colour=0xdd7878, title="Help: Private", type='rich',
                                  description=f'Syntax: `$private`{new_line}{new_line}'
                                              f'Creates a private channel that will be deleted after 1 hour.')
            await ctx.send(embed=embed)
        case "infra":
            embed = discord.Embed(colour=0xdd7878, title="Help: Infra", type='rich',
                                  description=f'Syntax: `$infra`{new_line}{new_line}'
                                              f'Displays your infrastructure.')
            await ctx.send(embed=embed)
        case "mstats":
            embed = discord.Embed(colour=0xdd7878, title="Help: Mstats", type='rich',
                                  description=f'Syntax: `$mstats`{new_line}{new_line}'
                                              f'Displays your military statistics.')
            await ctx.send(embed=embed)
        case "rename":
            embed = discord.Embed(colour=0xdd7878, title="Help: Rename", type='rich',
                                  description=f'Syntax: `$rename [new name]`{new_line}{new_line}'
                                              f'Changes the name of your nation to the [new name].{new_line}'
                                              f'Mind that the name cannot be longer than 25 characters.')
            await ctx.send(embed=embed)

        case "stats":
            embed = discord.Embed(colour=0xdd7878, title="Help: Stats", type='rich',
                                  description=f'Syntax: `$stats`{new_line}{new_line}'
                                              f'Displays your nation\'s statistics.')
            await ctx.send(embed=embed)

        case _:   # Actual command list
            generating = discord.Embed(colour=0xdce0e8, title="Help", type='rich',
                                       description="Generating help pages...")

            gen_emb = discord.Embed(colour=0xea76cb, title="Help | General", type='rich')   # General Tab
            gen_emb.add_field(name="Statistic Visualization", value="Stats - Displays your stats.\n"
                                                                    "Mstats - Displays your military stats.\n"
                                                                    "Infra - Displays your infrastructure.",
                              inline=False)
            gen_emb.add_field(name="Other Features", value="Private - Creates a private channel.\n"
                                                           "Create - Creates a nation.",
                              inline=False)

            eco_emb = discord.Embed(colour=0xdf8e1d, title="Help | Economy", type='rich')   # Economy Tab
            eco_emb.add_field(name="Category", value="Command - Description",
                              inline=False)

            tec_emb = discord.Embed(colour=0x04a5e5, title="Help | Technology", type='rich')   # Technology Tab
            tec_emb.add_field(name="Category", value="Command - Description",
                              inline=False)

            cus_emb = discord.Embed(colour=0x7287fd, title="Help | Customization", type='rich')   # Customization Tab
            cus_emb.add_field(name="Name Changing", value="Rename - Changes your name to something else.",
                              inline=False)

            set_emb = discord.Embed(colour=0x7c7f93, title="Help | Settings", type='rich')   # Settings Tab
            set_emb.add_field(name="Category", value="Command - Description",
                              inline=False)

            mil_emb = discord.Embed(colour=0xe64553, title="Help | Military", type='rich')   # Military Tab
            mil_emb.add_field(name="Category", value="Command - Description",
                              inline=False)

            pol_emb = discord.Embed(colour=0x8839ef, title="Help | Politics", type='rich')   # Politics Tab
            pol_emb.add_field(name="Category", value="Command - Description",
                              inline=False)

            adm_emb = discord.Embed(colour=0x40a02b, title="Help | Administration", type='rich')   # Administration Tab
            adm_emb.add_field(name="Category", value="Command - Description",
                              inline=False)

            help_emb = await ctx.send(embed=generating)   # Prepares Embed
            await help_emb.add_reaction('📊')
            await help_emb.add_reaction('💶')
            await help_emb.add_reaction('🧪')
            await help_emb.add_reaction('🖍️')
            await help_emb.add_reaction('🔨')
            await help_emb.add_reaction('💥')
            await help_emb.add_reaction('📜')
            await help_emb.add_reaction('✒️')
            match cmd:   # Chooses first page depending on [cmd]
                case "eco" | "economy":
                    await help_emb.edit(embed=eco_emb)
                case "tec" | "tech" | "technology":
                    await help_emb.edit(embed=tec_emb)
                case "cus" | "custom" | "customization":
                    await help_emb.edit(embed=cus_emb)
                case "set" | "settings":
                    await help_emb.edit(embed=set_emb)
                case "mil" | "military":
                    await help_emb.edit(embed=mil_emb)
                case "pol" | "politics" | "politic":
                    await help_emb.edit(embed=pol_emb)
                case "adm" | "admin" | "pop" | "population" | "administration":
                    await help_emb.edit(embed=adm_emb)
                case _:
                    await help_emb.edit(embed=gen_emb)

            def chk(rec, usr):
                return usr == ctx.author and str(rec.emoji) in ['📊', '💶', '🧪', '🖍️', '🔨', '💥', '📜', '✒️']

            while True:
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=60, check=chk)
                except TimeoutError:
                    break
                match(str(reaction.emoji)):   # Choosing Tab based on emoji
                    case '📊':
                        await help_emb.edit(embed=gen_emb)
                    case '💶':
                        await help_emb.edit(embed=eco_emb)
                    case '🧪':
                        await help_emb.edit(embed=tec_emb)
                    case '🖍️':
                        await help_emb.edit(embed=cus_emb)
                    case '🔨':
                        await help_emb.edit(embed=set_emb)
                    case '💥':
                        await help_emb.edit(embed=mil_emb)
                    case '📜':
                        await help_emb.edit(embed=pol_emb)
                    case '✒️':
                        await help_emb.edit(embed=adm_emb)
                    case _:
                        break
                await help_emb.remove_reaction(reaction.emoji, user)


@bot.command()   # Help command and command list made specifically for devs
async def devhelp(ctx, cmd: str = ""):
    if dev_check(ctx.author.id):
        global debug
        cmd = cmd.lower()
        match cmd:
            case "debug_mode" | "debugmode":
                embed = discord.Embed(colour=0xdc8a78, title="Dev Help | Debug Mode", type='rich',
                                      description=f'Syntax: `$debug_mode`{new_line}{new_line}'
                                                  f'Status: {debug}{new_line}{new_line}'
                                                  f'Switches the global variable \'debug\' from on to off and vice versa. {new_line}'
                                                  f'While on, this can do many things, but for now it only disables the error handler and prints the error to the console.{new_line}'
                                                  f'Debug mode is switched to off on boot.')
                await ctx.send(embed=embed)
            case "debug" | "debug_status" | "debugstatus" | "dstatus":
                embed = discord.Embed(colour=0xdc8a78, title="Dev Help | Debug Status", type='rich',
                                      description=f'Syntax: `$debug_status`{new_line}{new_line}'
                                                  f'Status: {debug}{new_line}{new_line}'
                                                  f'Shows whether debug mode is on or off')
                await ctx.send(embed=embed)
            case _:
                embed = discord.Embed(colour=0xdc8a78, title="Help | General", type='rich')  # General Tab
                embed.add_field(name="Debug", value="debug_mode - Turns debug mode on and off.\n"
                                                    "debug_status - Shows if debug mode is on or off.",
                                inline=False)
                await ctx.send(embed=embed)
    else:
        print(f'{ctx.author} attempted to enable debug')
        await ctx.send(f'Permission denied: You are not a developer.')


bot.run('INSERT BOT TOKEN HERE')
