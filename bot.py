import os
import timestamp
import config
import custom_logging
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
    """<command> - Specify a command, outputs commands if none is given."""
    log.log_command(ctx.author, "help")
    _commands = "\n".join([str(command) for command in bot.commands])
    if not command:
        await ctx.send(f"List of commands:```\n{_commands}```Specify a command for more information.")
    else:
        for _command in bot.commands:
            if str(_command) == command.lower():
                tmp = _command
                await ctx.send(f"```\n{str(command)} {tmp.help}```")
                break
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
