import discord


class MusicButtons(discord.ui.View):
    def __init__(self, client, musicController):
        super().__init__(timeout=None)
        self.tree = client.tree
        self.musicController = musicController

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=0)
    async def PauseResume_Button(self, interaction: discord.Interaction, Button: discord.ui.Button):
        response = await self.musicController.pauseSong()
        if response:
            Button.label = "▶"
            await interaction.response.edit_message(view=self)
        else:
            Button.label = "⏸"
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.secondary, row=0)
    async def Skip_Button(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.tree.get_command("skip").callback(interaction)

    @discord.ui.button(label="⏹", style=discord.ButtonStyle.secondary, row=0)
    async def Stop_Button(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.tree.get_command("stop").callback(interaction)

    @discord.ui.button(label="⟳", style=discord.ButtonStyle.secondary, row=0)
    async def Loop_Button(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.tree.get_command("loop").callback(interaction)

    @discord.ui.button(label="⇄", style=discord.ButtonStyle.secondary, row=1)
    async def Shuffle_Button(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.tree.get_command("shuffle").callback(interaction)

    @discord.ui.button(label="☰", style=discord.ButtonStyle.secondary, row=1)
    async def Queue_Button(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.tree.get_command("queue").callback(interaction)

    @discord.ui.button(label="⊘", style=discord.ButtonStyle.secondary, row=1)
    async def Kick_Button(self, interaction: discord.Interaction, Button: discord.ui.Button):
        await self.tree.get_command("dc").callback(interaction)
