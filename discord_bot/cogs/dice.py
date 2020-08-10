import discord, random
from discord.ext import commands
from discord.utils import get

class DiceCog(commands.Cog, name="Dice Cog"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='dice')
    async def dice(self, ctx, roll):
        splits = roll.split("d")
#        try:
        if len(splits) != 2:
            await ctx.send("Please roll dice using the format e.g. \"2d20\" to roll two twenty-sided dice")
        else:
            if len(splits[0]) == 0:
                splits[0] = "1"
            rolls = []
            for die in range(int(splits[0])):
                rolls.append(random.randrange(1,int(splits[1])+1))
            summation = sum(int(i) for i in rolls)
            await ctx.send(f"""**{summation}**; Rolls: {rolls}""")
#        except Exception as e:
#            await ctx.send(f'**`ERROR:`** {type(e).__name__} - {e}')

def setup(bot):
    bot.add_cog(DiceCog(bot))