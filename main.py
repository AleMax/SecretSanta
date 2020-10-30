import discord
import sqlite3
import random
import asyncio

intents = discord.Intents.default()
intents.members = True
#intents.presences = True

token = ''
prefix = 'ss!'

conn = sqlite3.connect('database.db')
c = conn.cursor()


class SecretSanta(discord.Client):
    async def on_ready(self):
        print('Logged on as {0}!'.format(self.user))
        await client.change_presence(activity=discord.Game(name='Secret Santa'))

    async def on_message(self, message):
        if message.author == client.user:
            return
        author = message.author
        channel = message.channel
        if not author.bot:

            if message.content.lower().startswith(prefix + 'help'):
                embed = discord.Embed(color=0xfdfdfd)
                embed.title = "Secret Santa Help"
                avatar_url = client.user.avatar_url
                if avatar_url is not None:
                    embed.set_thumbnail(url=avatar_url)
                helptext = "**Prefix:** `" + prefix + "`\n"
                helptext_normal = """
`help` - Displays help about the bot!
`join [name]` - Join a Secret Santa!
`leave [name]` - Leave a Secret Santa!
`info [name]` - Get info about a running Secret Santa!
                """
                helptext_moderator = """
`create [name]` - Creates a Secret Santa for your server.
`start [name]` - Starts a Secret Santa after people have joined.
                """
                helptext_dm = """
`status` - See information about all the Secret Santas you joined.
`wish [wish]` - Help your match by giving him advice about what he could gift you!
`clearwish` - Clear your wish if you rather want to be fully surprised.
`submit [name]` - Start the submission process for the given Secret Santa!
`clearsubmission [name]` - Clears all submissions you gave for that Secret Santa.
                                """
                embed.description = helptext
                embed.add_field(name="Default", value=helptext_normal)
                embed.add_field(name="DM Only", value=helptext_dm)
                embed.add_field(name="Moderator", value=helptext_moderator)
                await channel.send(embed=embed)

            if isinstance(channel, discord.DMChannel):

                if (prefix + 'wish').lower() in message.content.lower():
                    c.execute("SELECT * FROM Users WHERE user_id=" + str(author.id))
                    user = c.fetchone()
                    if user is None:
                        c.execute("INSERT INTO Users VALUES (" + str(author.id) + ", NULL)")

                    if message.content.lower() == (prefix + 'wish').lower():
                        wishtext = None
                        if user is not None:
                            wishtext = user[1]
                        if wishtext is None:
                            await channel.send('You have no wish set so far!\nSet one with `' + prefix + 'wish [text]`!')
                        else:
                            embed = discord.Embed(color=0xfdfdfd)
                            embed.title = author.name + "'s wish"
                            avatar_url = author.avatar_url
                            if avatar_url is not None:
                                embed.set_thumbnail(url=avatar_url)
                            embed.description = wishtext
                            await channel.send(embed=embed)

                    elif message.content.lower().startswith(prefix + 'wish '):
                        prefix_length = len(prefix + 'wish ')
                        wishtext = message.content[prefix_length:]
                        if len(wishtext) > 0:
                            c.execute("UPDATE Users SET wish='" + wishtext + "' WHERE user_id=" + str(author.id))
                            embed = discord.Embed(color=0xfdfdfd)
                            embed.title = "Succesfully changed " + author.name + "'s wish to"
                            avatar_url = author.avatar_url
                            if avatar_url is not None:
                                embed.set_thumbnail(url=avatar_url)
                            embed.description = wishtext
                            await channel.send(embed=embed)
                        else:
                            await channel.send('Please enter a wish!\nSet one with `' + prefix + 'wish [text]`!')

                elif message.content.lower().startswith(prefix + 'clearwish'):
                    c.execute("SELECT * FROM Users WHERE user_id=" + str(author.id))
                    user = c.fetchone()
                    if user is None:
                        c.execute("INSERT INTO Users VALUES (" + str(author.id) + ", NULL)")
                    c.execute("UPDATE Users SET wish=NULL WHERE user_id=" + str(author.id))
                    await channel.send('Successfully cleared your wish!')

                elif message.content.lower().startswith(prefix + 'submit'):
                    prefix_length = len(prefix + 'submit ')
                    if len(message.content) > prefix_length:
                        ss_id = message.content[prefix_length:]
                        c.execute("SELECT * FROM List WHERE ss_id like '" + ss_id + "'")
                        ss = c.fetchone()
                        if ss is None:
                            await channel.send('There is no Secret Santa with the name `' + ss_id + "`!")
                        elif ss[2] == 0:
                            await channel.send("This Secret Santa hasn't started yet, be a bit patient!")
                        elif ss[2] != 1:
                            await channel.send("Submissions for this Secret Santa arent open anymore.")
                        else:
                            c.execute("SELECT * FROM Entries WHERE ss_id like '" + ss_id + "' and user_id=" + str(author.id))
                            entry = c.fetchone()
                            if entry is None:
                                await channel.send("You didn't join this Secret Santa!")
                            else:
                                messages = []
                                await channel.send("You can now send messages and attach files like Images to them.\nEvery message you send here will be recorded and sent to your match later!\nIf you finished with your messages type `" + prefix + "stop` to stop the recording!")

                                def check(checked_message):
                                    return message.channel == checked_message.channel and message.author == checked_message.author

                                while True:
                                    try:
                                        new_message = await client.wait_for('message', timeout=600.0, check=check)
                                    except asyncio.TimeoutError:
                                        await channel.send("Waiting for messages timed out after 10 Minutes! Saved all messages so far sent, if you want to add to your submission, just start the submission process again!\nYou can also clear your submission with `" + prefix + "clearsubmission [name]`")
                                        break
                                    else:
                                        if new_message.content.lower().startswith(prefix + 'stop'):
                                            await channel.send("You saved your submission! If you want to add to your submission, just start the submission process again!\nYou can also clear your submission with `" + prefix + "clearsubmission [name]`")
                                            break
                                        else:
                                            messages.append(new_message.id)

                                for m_id in messages:
                                    c.execute("INSERT INTO Submissions VALUES ('" + ss_id + "', " + str(author.id) + ", " + str(m_id) + ")")
                                    c.execute("UPDATE Entries SET submitted=1 WHERE ss_id like '" + ss_id + "' AND user_id=" + str(author.id))
                    else:
                        await channel.send('Please add the name of the secret santa you want to submit to!')

                elif message.content.lower().startswith(prefix + 'clearsubmission'):
                    prefix_length = len(prefix + 'clearsubmission ')
                    if len(message.content) > prefix_length:
                        ss_id = message.content[prefix_length:]
                        c.execute("SELECT * FROM List WHERE ss_id like '" + ss_id + "'")
                        ss = c.fetchone()
                        if ss is None:
                            await channel.send('There is no Secret Santa with the name *' + ss_id + "*!")
                        elif ss[2] == 0:
                            await channel.send("This Secret Santa hasn't started yet, be a bit patient!")
                        elif ss[2] != 1:
                            await channel.send("Submissions for this Secret Santa arent open anymore.")
                        else:
                            c.execute("SELECT * FROM Entries WHERE ss_id like '" + ss_id + "' and user_id=" + str(author.id))
                            entry = c.fetchone()
                            if entry is None:
                                await channel.send("You didn't join this Secret Santa!")
                            else:
                                c.execute("DELETE FROM Submissions WHERE ss_id like '" + ss_id + "' and user_id=" + str(author.id))
                                c.execute("UPDATE Entries SET submitted=0 WHERE ss_id like '" + ss_id + "' AND user_id=" + str(author.id))
                                await channel.send('You cleared all your submissions for the Secret Santa `' + ss_id + "`!")
                    else:
                        await channel.send('Please add the name of the secret santa you want to clear the submissions from!')

                elif message.content.lower().startswith(prefix + 'status'):
                    embed = discord.Embed(color=0xfdfdfd)
                    embed.title = author.name + "'s Secret Santa Status"
                    avatar_url = author.avatar_url
                    if avatar_url is not None:
                        embed.set_thumbnail(url=avatar_url)

                    c.execute("SELECT ss_id, match, submitted FROM Entries WHERE user_id=" + str(author.id))
                    ss_list = c.fetchall()
                    joined = ""
                    for ss in ss_list:
                        joined += ss[0]
                        if ss[1] is not None:
                            joined += "\t- " + client.get_user(ss[1]).name + "\t- " + str(ss[2] == 1)
                        joined += "\n"

                    c.execute("SELECT * FROM Users WHERE user_id=" + str(author.id))
                    user = c.fetchone()

                    wishtext = "*No wish set so far!*"
                    if user is not None:
                        wishtext = user[1]

                    embed.add_field(name="Name - Match - Submitted", value=joined)
                    embed.add_field(name="Your Wish", value=wishtext)

                    await channel.send(embed=embed)


            elif isinstance(channel, discord.TextChannel):

                if message.content.lower().startswith(prefix + 'join'):
                    prefix_length = len(prefix + 'join ')
                    if len(message.content) > prefix_length:
                        ss_id = message.content[prefix_length:]
                        c.execute("SELECT * FROM List WHERE ss_id like '" + ss_id + "'")
                        ss = c.fetchone()
                        if ss is None or ss[1] != message.guild.id:
                            await channel.send('There is no Secret Santa with the name `' + ss_id + "`!")
                        elif ss[2] != 0:
                            await channel.send("This Secret Santa started already and you cant join anymore unfortunately")
                        else:
                            c.execute("SELECT * FROM Entries WHERE ss_id like '" + ss_id + "' and user_id=" + str(author.id))
                            entry = c.fetchone()
                            if entry is not None:
                                await channel.send("You already joined this Secret Santa!")
                            else:
                                try:
                                    dm_channel = author.dm_channel
                                    if dm_channel is None:
                                        dm_channel = await author.create_dm()
                                    await dm_channel.send("You joined the Secret Santa `" + ss_id + """`!
You will be assigned a random person after the Secret Santa has started.
If you want to help the person who you will be assigned to, you can use `""" + prefix + """wish` to simply give them some ideas of what the person can gift you (if you want to get a full suprise you can also just not set a wish). They will be able to see what you set as your wish after the Secret Santa has started!""")
                                except:
                                    await channel.send("I was not able to DM you!\nIt is absolutely necessary for me to be able to DM you to properly execute the Secret Santa. So please enable DMs for this Server and join again!")
                                else:
                                    c.execute("INSERT INTO Entries VALUES ('" + ss_id + "', " + str(author.id) + ", NULL, 0)")
                                    await channel.send('You successfully joined the Secret Santa `' + ss_id + "`!")
                    else:
                        await channel.send('To join a Secret Santa use `' + prefix + 'join [name]`!')

                elif message.content.lower().startswith(prefix + 'leave'):
                    prefix_length = len(prefix + 'leave ')
                    if len(message.content) > prefix_length:
                        ss_id = message.content[prefix_length:]
                        c.execute("SELECT * FROM List WHERE ss_id like '" + ss_id + "'")
                        ss = c.fetchone()
                        if ss is None or ss[1] != message.guild.id:
                            await channel.send('There is no Secret Santa with the name `' + ss_id + "`!")
                        elif ss[2] != 0:
                            await channel.send("This Secret Santa started already and you cant leave anymore!\nDon't try to avoid your responsibilities!")
                        else:
                            c.execute("SELECT * FROM Entries WHERE ss_id like '" + ss_id + "' and user_id=" + str(author.id))
                            entry = c.fetchone()
                            if entry is None:
                                await channel.send("You didn't join this Secret Santa!")
                            else:
                                c.execute("DELETE FROM Entries WHERE ss_id like '" + ss_id + "' and user_id=" + str(author.id))
                                await channel.send('You successfully left the Secret Santa `' + ss_id + "`!")
                    else:
                        await channel.send('To leave a Secret Santa use `' + prefix + 'leave [name]`!')

                elif message.content.lower().startswith(prefix + 'info'):
                    prefix_length = len(prefix + 'info ')
                    if len(message.content) > prefix_length:
                        ss_id = message.content[prefix_length:]
                        c.execute("SELECT * FROM List WHERE ss_id like '" + ss_id + "'")
                        ss = c.fetchone()
                        if ss is None or ss[1] != message.guild.id:
                            await channel.send('There is no Secret Santa with the name `' + ss_id + "`!")
                        else:
                            c.execute("SELECT * FROM Entries WHERE ss_id like '" + ss_id + "'")
                            entries = c.fetchall()
                            participants = ""
                            for entry in entries:
                                user = client.get_user(entry[1])
                                if user is not None:
                                    participants += client.get_user(entry[1]).name + "\n"
                                else:
                                    participants += str(entry[1]) + "\n"
                            embed = discord.Embed(color=0xfdfdfd)
                            embed.title = ss_id
                            if len(participants) != 0:
                                embed.add_field(name="Participants", value=participants)
                            status = "Created"
                            if ss[2] == 1:
                                status = "Started"
                            elif ss[2] == 2:
                                status = "Closed"
                            embed.add_field(name="Status", value=status)
                            await channel.send(embed=embed)
                    else:
                        await channel.send('To see information about a Secret Santa use `' + prefix + 'info [name]`!')

                perms = author.guild_permissions
                if perms.manage_messages:

                    if message.content.lower().startswith(prefix + 'create'):
                        prefix_length = len(prefix + 'create ')
                        if len(message.content) > prefix_length:
                            ss_id = message.content[prefix_length:]

                            if ss_id.isalnum():
                                c.execute("SELECT * FROM List WHERE ss_id like '" + ss_id + "'")
                                ss = c.fetchone()
                                if ss is not None:
                                    await channel.send('Please use a different name, `' + ss_id + "` is already in use!")
                                else:
                                    c.execute("INSERT INTO List VALUES ('" + ss_id + "', " + str(message.guild.id) + ", 0)")
                                    await channel.send('Secret Santa *' + ss_id + '* successfully created')
                            else:
                                await channel.send('Please use only alphanumeric characters as a name!')
                        else:
                            await channel.send('To create a new Secret Santa use `' + prefix + 'create [name]`!')

                    elif message.content.lower().startswith(prefix + 'start'):
                        prefix_length = len(prefix + 'start ')
                        if len(message.content) > prefix_length:
                            ss_id = message.content[prefix_length:]
                            c.execute("SELECT * FROM List WHERE ss_id like '" + ss_id + "'")
                            ss = c.fetchone()
                            if ss is None or ss[1] != message.guild.id:
                                await channel.send('There is no Secret Santa with the name `' + ss_id + "`!")
                            elif ss[2] != 0:
                                await channel.send("This Secret Santa started already, you cant start it twice!")
                            else:
                                c.execute("SELECT user_id FROM Entries WHERE ss_id like '" + ss_id + "'")
                                entries = c.fetchall()
                                if len(entries) < 2:
                                    await channel.send("There need to be at least 2 participants in the Secret Santa!")
                                else:
                                    c.execute("UPDATE List SET phase=1 WHERE ss_id like '" + ss_id + "'")
                                    participants = []
                                    for entry in entries:
                                        participants.append(entry[0])
                                    random_part = participants[:]
                                    while True:
                                        random.shuffle(random_part)
                                        for a, b in zip(participants, random_part):
                                            if a == b:
                                                break
                                        else:
                                            break
                                    for a, b in zip(participants, random_part):
                                        c.execute("UPDATE Entries SET match=" + str(b) + " WHERE ss_id like '" + ss_id + "' and user_id=" + str(a))
                                        dm_channel = client.get_user(a).dm_channel
                                        if dm_channel is None:
                                            dm_channel = await client.get_user(a).create_dm()

                                        await dm_channel.send("You have been assigned " + client.get_user(b).name + "!\nYou can submit your gift via the `" + prefix + "submit " + ss_id + "` command!")

                                        c.execute("SELECT * FROM Users WHERE user_id=" + str(client.get_user(b).id))
                                        user = c.fetchone()

                                        wishtext = None
                                        if user is not None:
                                            wishtext = user[1]
                                        if wishtext is None:
                                            await dm_channel.send('Your match has not set any wish. Feel free to be creative :)')
                                        else:
                                            embed = discord.Embed(color=0xfdfdfd)
                                            embed.title = client.get_user(b).name + "'s wish"
                                            avatar_url = client.get_user(b).avatar_url
                                            if avatar_url is not None:
                                                embed.set_thumbnail(url=avatar_url)
                                            embed.description = wishtext
                                            await dm_channel.send(embed=embed)


                        else:
                            await channel.send('To start a Secret Santa use `' + prefix + 'start [name]`!')




            conn.commit()


client = SecretSanta(intents=intents)
client.run(token)
