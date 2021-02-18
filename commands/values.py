import json
import aiohttp
import discord
import datetime
import config
import custom_logging
from bs4 import BeautifulSoup
from discord.ext import commands
from discord.ext.commands import cooldown, BucketType


class CryptoValues(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.log = custom_logging.Logging()

    async def convert_value(self, ctx, command: str, currency: str, amount):
        api_url = "https://api.exchangeratesapi.io/latest?base=USD"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url=api_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    resp = await response.read()
                    data = json.loads(resp)
                    return float(data["rates"][currency.upper()]) * amount, currency
            except Exception as error:
                await ctx.send(f"Failed to convert the value. Using USD to output.")
                self.log.log_error(error, command.upper())
                return amount, "usd"

    @commands.command(name="btc", aliases=["bitcoin"])
    @cooldown(1, int(config.COOLDOWN), BucketType.guild)
    # adding cooldown timer to prevent spamming requests
    async def btc(self, ctx, currency=None):
        """[currency] - *OPTIONAL* Specify a currency, defaults to USD if none is given."""
        self.log.log_command(ctx.author, "btc")
        currencies = ["usd", "eur", "aud", "rub"]
        if not currency:
            curr = currencies[0]
        else:
            if currency.lower() in currencies:
                curr = currency.lower()
            else:
                await ctx.send(f"This currency is not supported. Please use one of the supported types: {currencies}")
                return

        api_url = "https://api.coindesk.com/v1/bpi/currentprice.json"
        change_url = "https://www.coindesk.com/price/bitcoin"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url=api_url, timeout=aiohttp.ClientTimeout(total=5)) as response_value:
                    resp = await response_value.read()
                    data = json.loads(resp)
                    btc_value = data["bpi"]["USD"]["rate_float"]
                async with session.get(url=change_url, timeout=aiohttp.ClientTimeout(total=5)) as response_change:
                    resp = await response_change.read()
                    soup = BeautifulSoup(resp, "html.parser")
                    parse_change = soup.find("span", "percent-value-text")
            except Exception as error:
                await ctx.send(f"Failed to retrieve the current Bitcoin value.")
                self.log.log_error(error, "btc")
                return

        if curr != "usd":
            converted_value, curr = await self.convert_value(ctx, "btc", curr, btc_value)
        else:
            converted_value = btc_value
        _value = round(converted_value, 2)
        embed = discord.Embed(title="Bitcoin Value", description=f"{_value:,} {curr.upper()} ({'+' if float(parse_change.text) > 0 else ''}{parse_change.text}%)", colour=0xF6FA00, timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f"CoinDesk API")
        await ctx.send(embed=embed)

    @commands.command(name="eth", aliases=["ethereum"])
    @cooldown(1, int(config.COOLDOWN), BucketType.guild)
    # adding cooldown timer to prevent spamming requests
    async def eth(self, ctx, currency=None):
        """[currency] - *OPTIONAL* Specify a currency, defaults to USD if none is given."""
        self.log.log_command(ctx.author, "eth")
        currencies = ["usd", "eur", "aud", "rub"]
        if not currency:
            curr = currencies[0]
        else:
            if currency.lower() in currencies:
                curr = currency.lower()
            else:
                await ctx.send(f"This currency is not supported. Please use one of the supported types: {currencies}")
                return

        api_url = "https://data.messari.io/api/v1/assets/eth/metrics"
        change_url = "https://www.coindesk.com/price/ethereum"
        async with aiohttp.ClientSession() as session:
            try:
                # increased timeout value because API response time is slow
                async with session.get(url=api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    resp = await response.read()
                    data = json.loads(resp)
                    eth_value = data["data"]["market_data"]["price_usd"]
                async with session.get(url=change_url, timeout=aiohttp.ClientTimeout(total=5)) as response_change:
                    resp = await response_change.read()
                    soup = BeautifulSoup(resp, "html.parser")
                    parse_change = soup.find("span", "percent-value-text")
            except Exception as error:
                await ctx.send(f"Failed to retrieve the current Ethereum value.")
                self.log.log_error(error, "eth")
                return

        if curr != "usd":
            converted_value, curr = await self.convert_value(ctx, "eth", curr, eth_value)
        else:
            converted_value = eth_value
        _value = round(converted_value, 2)
        embed = discord.Embed(title="Ethereum Value", description=f"{_value:,} {curr.upper()} ({'+' if float(parse_change.text) > 0 else ''}{parse_change.text}%)", colour=0xecf0f1, timestamp=datetime.datetime.utcnow())
        embed.set_footer(text=f"Messari API")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(CryptoValues(bot))
