import os
import discord
import json
import datetime
import asyncio
import aiohttp
import custom_logging
from discord.ext import commands


class CryptoMonitor(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.currency = None
        self.channel = None
        self.monitor = None
        self.interval = None
        self.status = None
        self.reset = False
        self.run = False
        self.log = custom_logging.Logging()

    async def get_prices(self):
        btc_value = 0
        eth_value = 0

        api_url = "https://api.coindesk.com/v1/bpi/currentprice.json"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url=api_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    resp = await response.read()
                    data = json.loads(resp)
                    btc_value = data["bpi"]["USD"]["rate_float"]
            except Exception as error:
                self.log.log_error(error, "btc_monitor")

        api_url = "https://data.messari.io/api/v1/assets/eth/metrics"
        async with aiohttp.ClientSession() as session:
            try:
                # increased timeout value because API response time is slow
                async with session.get(url=api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    resp = await response.read()
                    data = json.loads(resp)
                    eth_value = data["data"]["market_data"]["price_usd"]
            except Exception as error:
                self.log.log_error(error, "eth_monitor")

        if 0 in (btc_value, eth_value):
            self.status = "Having issues with the crypto API"
        return btc_value, eth_value

    async def convert_value(self, currency):
        api_url = "https://api.exchangeratesapi.io/latest?base=USD"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url=api_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    resp = await response.read()
                    data = json.loads(resp)
                    return float(data["rates"][currency.upper()])
            except Exception as error:
                self.log.log_error(error, "convert_monitor")
                self.status = "Having issues with the conversion API"
                return 1

    @commands.command(name="run", aliases=["go"])
    @commands.has_permissions(administrator=True)
    async def loop_monitor(self, ctx, interval=None):
        """[interval] - *OPTIONAL* Specify a delay between checks, defaults to 1 minute if none is given."""
        self.log.log_command(ctx.author, "run")
        if not self.channel:
            with open("settings.txt", "r") as settings_input:
                data = json.load(settings_input)
            if data["setup"]:
                await ctx.send("Please reset the monitor and initialize it again.")
            else:
                await ctx.send("Monitor has not been initialized yet.")
        else:
            if self.run:
                await ctx.send("Monitor is already running.")
                return
            if not interval:
                self.interval = 1
            else:
                try:
                    self.interval = int(interval)
                    if not (60 >= self.interval >= 1):
                        await ctx.send("Use an integer between 1 and 60.")
                        return
                except Exception as error:
                    self.log.log_error(error, "run")
                    await ctx.send("Invalid datatype, provide an integer.")
                    return

            self.run = True
            await ctx.send(f"Running the monitor with a delay of {self.interval}.")
            while not self.reset:
                self.status = f"Running using an interval of {self.interval} {'minute' if self.interval == 1 else 'minutes'}"
                btc_price, eth_price = await self.get_prices()
                if self.currency != "usd":
                    curr_value = await self.convert_value(self.currency)
                    btc_price, eth_price = btc_price * curr_value, eth_price * curr_value

                embed = discord.Embed(title="Crypto Monitor", description=f"**STATUS**: {self.status}", colour=0x0059b3, timestamp=datetime.datetime.utcnow())
                embed.add_field(name="Bitcoin", value=f"{round(btc_price, 2):,} {self.currency.upper()}")
                embed.add_field(name="Ethereum", value=f"{round(eth_price, 2):,} {self.currency.upper()}")
                embed.set_footer(text=f"Powered by CoinDesk & Messari")

                await self.monitor.edit(embed=embed)
                await asyncio.sleep(self.interval * 60)

    @commands.command(name="setup", aliases=["start"])
    @commands.has_permissions(administrator=True)
    async def setup_monitor(self, ctx, name=None):
        """[name] - *OPTIONAL* Specify a channel name, defaults to crypto if none is given."""
        self.log.log_command(ctx.author, "setup")
        try:
            with open("settings.txt", "r") as settings_input:
                data = json.load(settings_input)
                self.currency = data["currency"]
                if data["setup"]:
                    await ctx.send("Setup has already been performed.")
                    return
                if not name:
                    name = data["name"]
                for channel in ctx.guild.channels:
                    if channel.name == name:
                        await ctx.send("Duplicate channel name, could not create channel.")
                        return
                else:
                    with open("settings.txt", "w") as settings_output:
                        tmp = {"name": name.lower(), "currency": data["currency"], "setup": True}
                        json.dump(tmp, settings_output, indent=4)
                    self.channel = await discord.Guild.create_text_channel(ctx.guild, name=name.lower(), topic="a dedicated channel for the monitor", reason="channel for crypto monitor")
                    embed = discord.Embed(title="Crypto Monitor", description=f"Use the run command to start the monitor.", colour=0x0059b3, timestamp=datetime.datetime.utcnow())
                    embed.set_footer(text=f"Powered by CoinDesk & Messari")
                    self.monitor = await self.channel.send(embed=embed)
                    self.reset = False
                    await ctx.send(f"Created a new monitor with the name {str(name).upper()}")
        except Exception as error:
            await ctx.send("Could not retrieve monitor settings.")
            self.log.log_error(error, "start")
            return

    @commands.command(name="edit", aliases=["change", "config"])
    @commands.has_permissions(administrator=True)
    async def edit_currency_monitor(self, ctx, currency=None):
        """<currency> - *REQUIRED* Specify a currency to edit the monitor's display with."""
        self.log.log_command(ctx.author, "edit")
        try:
            with open("settings.txt", "r") as settings_input:
                data = json.load(settings_input)
                if not data["setup"]:
                    await ctx.send("Monitor has not been initialized yet.")
                    return
                elif not currency:
                    await ctx.send("Please specify a currency for the monitor.")
                    return
                else:
                    currencies = ["usd", "eur", "aud", "rub"]
                    if str(currency).lower() in currencies:
                        with open("settings.txt", "w") as settings_output:
                            self.currency = str(currency).lower()
                            tmp = {"name": data["name"], "currency": str(currency).lower(), "setup": data["setup"]}
                            json.dump(tmp, settings_output, indent=4)
                            await ctx.send(f"Changed the monitor's currency to {str(currency).upper()}.")
                    else:
                        await ctx.send(f"This currency is not supported. Please use one of the supported types: {currencies}")
                        return
        except Exception as error:
            await ctx.send("Could not retrieve monitor settings.")
            self.log.log_error(error, "start")
            return

    @commands.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def reset_monitor(self, ctx, name=None):
        """<monitor> - *REQUIRED* Specify a monitor name to reset the settings."""
        self.log.log_command(ctx.author, "reset")
        if not name:
            await ctx.send("Pass the monitor's name as argument to confirm the reset.")
            return
        for channel in ctx.guild.channels:
            if channel.name == name:
                try:
                    self.reset = True
                    self.run = False
                    await channel.delete()
                    # removing the file in case encoding issues occurred
                    os.remove("settings.txt")
                    self.currency = "usd"
                    with open("settings.txt", "w") as settings_output:
                        tmp = {"name": "crypto", "currency": "usd", "setup": False}
                        json.dump(tmp, settings_output, indent=4)
                    await ctx.send("Settings have been reset and the monitor has been deleted.")
                    return
                except Exception as error:
                    await ctx.send("Something went wrong, check the logs.")
                    self.log.log_error(error, "reset")
                    return
        else:
            await ctx.send("No monitor found with that name.")


def setup(bot):
    bot.add_cog(CryptoMonitor(bot))
