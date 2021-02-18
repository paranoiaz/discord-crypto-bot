import os
import timestamp
import config
import custom_logging
import discord
import datetime
from discord.ext import commands

bot = commands.Bot(command_prefix=config.PREFIX, help_command=None, case_insensitive=True)


@bot.event
async def on_command_error(ctx, exception):
    if isinstance(exception, commands.CommandOnCooldown):
        await ctx.send(f"Command is on cooldown, try again in {exception.retry_after:0.2}s")
    elif isinstance(exception, commands.CommandInvokeError):
        await ctx.send("I have no permission to perform this.")
    elif isinstance(exception, commands.CommandNotFound):
        await ctx.send("This is not a valid command.")
    # used for monitor commands
    elif isinstance(exception, commands.MissingPermissions):
        await ctx.send("You have no permission to use this command.")


@bot.command(name="help", aliases=["commands"])
async def help(ctx, command=None):
    """[command] - *OPTIONAL* Specify a command, outputs commands if none is given."""
    log.log_command(ctx.author, "help")
    _commands = "\n".join([str(command) for command in bot.commands])
    help_embed = discord.Embed(title="Crypto Bot", description=f"List of commands and their parameters:", colour=0x00CC00, timestamp=datetime.datetime.utcnow())
    help_embed.set_footer(text=f"Specify a command for more information")

    for _command in bot.commands:
        if not command:
            help_embed.add_field(name=f"{str(_command)}", value=f"{_command.help.split('-')[0]}")
        else:
            if str(_command) == command.lower():
                await ctx.send(f"```\n{str(_command)} {_command.help}```")
                return

    if not command:
        await ctx.send(embed=help_embed)
    else:
        await ctx.send(f"Command not found, please use a valid one.")


if __name__ == "__main__":
    print(f"{timestamp.timestamp()} CryptoBot developed by github.com/paranoiaz")
    log = custom_logging.Logging()
    for file in os.listdir("./commands"):
        if file.endswith(".py"):
            try:
                cog = file.split(".py")[0]
                bot.load_extension(f"commands.{cog}")
                print(f"{timestamp.timestamp()} Successfully loaded cog: {cog}")
            except Exception as error:
                print(f"{timestamp.timestamp()} Failed to load cog: {file} - {repr(error)}")
    bot.run(config.TOKEN)
