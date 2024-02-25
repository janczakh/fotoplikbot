import sqlite3
import time

import discord
from discord import app_commands


def variety(base: str, num: int) -> str:
    return f'{num} {base}{"kę" if num == 1 else "ki" if 1 < num < 5 else "ek"}'


def parse_table(input: list[tuple[int]]) -> str:
    return '\n'.join([f'* <t:{int(record[1])}> <@{record[2]}> {record[3]}'
                      for record in input])


class Client(discord.Client):
    def __init__(self, *, intents: discord.Intents) -> None:
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

        self.con = sqlite3.connect('dziennik.db')
        self.cur = self.con.cursor()
        
        self.cur.execute('CREATE TABLE IF NOT EXISTS jedymki (user_id INTEGER,'
                         'timestamp INTEGER, author_id INTEGER, messaeg_url INTEGER)')
        self.cur.execute('CREATE TABLE IF NOT EXISTS trzustki (user_id INTEGER,'
                         'timestamp INTEGER, author_id INTEGER, message_url INTEGER)')

    def __del__(self) -> None:
        self.con.commit()
        self.con.close()


    async def setup_hook(self) -> None:
        self.tree.copy_global_to(guild=discord.Object(id=1194344832802496664))
        await self.tree.sync(guild=discord.Object(id=1194344832802496664))


client = Client(intents=discord.Intents.default())


@client.tree.context_menu()
async def jedymka(interaction: discord.Interaction, message: discord.Message):
    client.cur.execute('INSERT INTO jedymki VALUES (?, ?, ?, ?)',
                            (message.author.id, time.time(),
                             interaction.user.id, message.jump_url))
    
    await interaction.response.send_message(f'{message.author.mention} '
                                             'otrzymał(-a) **jedymkę** od '
                                            f'{interaction.user.mention} w '
                                             'związku z wiadomością '
                                            f'{message.jump_url}')


@client.tree.context_menu()
async def trzustka(interaction: discord.Interaction, message: discord.Message):
    if message.author == interaction.user:
        return await interaction.response.send_message('Nie możesz dać '
                                                       'trzustki sam sobie, '
                                                       'ale możesz jedymkę!', 
                                                       ephemeral=True)
    
    client.cur.execute('INSERT INTO trzustki VALUES (?, ?, ?, ?)',
                       (message.author.id, time.time(), interaction.user.id,
                        message.jump_url))
    
    await interaction.response.send_message(f'{message.author.mention} '
                                             'otrzymał(-a) **trzustkę** od '
                                            f'{interaction.user.mention} w'
                                             ' związku z wiadomością '
                                            f'{message.jump_url}')


@client.tree.context_menu()
async def grades(interaction: discord.Interaction, member: discord.Member):
    client.cur.execute('SELECT * FROM jedymki WHERE user_id = ?', (member.id,))
    jedymki = client.cur.fetchall()

    client.cur.execute('SELECT * FROM trzustki WHERE user_id = ?', (member.id,))
    trzustki = client.cur.fetchall()
    
    await interaction.response.send_message(
        f'oceny {member.mention}\n## jedymki\n{parse_table(jedymki)}\n'
        f'## trzustki\n{parse_table(trzustki)}', silent=True)


@client.tree.context_menu()
async def average(interaction: discord.Interaction, member: discord.Member):
    client.cur.execute('SELECT * FROM jedymki WHERE user_id = ?', (member.id,))
    jedymki = len(client.cur.fetchall())

    client.cur.execute('SELECT * FROM trzustki WHERE user_id = ?', (member.id,))
    trzustki = len(client.cur.fetchall())

    await interaction.response.send_message(f'{member.mention} ma '
                                            f'**{variety("jedym", jedymki)}** '
                                            f'i **{variety("trzust", trzustki)}'
                                            f'**. Średnia to **'
                                            f'{(6*trzustki + jedymki) /
                                               (x if (x := jedymki + trzustki)
                                                > 0 else 1)}**.', silent=True)


if __name__ == '__main__':
    client.run('')
