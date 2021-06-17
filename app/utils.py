import aiohttp
import sentry_sdk
from discord.ext import commands

import config


def use_sentry(client, **sentry_args):
    """
    Use this compatibility library as a bridge between Discord and Sentry.
    Arguments:
        client: The Discord client object (e.g. `discord.AutoShardedClient`).
        sentry_args: Keyword arguments to pass to the Sentry SDK.
    """

    sentry_sdk.init(**sentry_args)

    @client.event
    async def on_error(event, *args, **kwargs):
        """Don't ignore the error, causing Sentry to capture it."""
        raise

    @client.event
    async def on_command_error(msg, error):
        # don't report errors to sentry related to wrong permissions
        if not isinstance(
            error,
            (
                commands.MissingRole,
                commands.MissingAnyRole,
                commands.BadArgument,
                commands.MissingRequiredArgument,
                commands.errors.CommandNotFound,
            ),
        ):
            raise error


async def fetch_alchemists_data() -> list:
    async with aiohttp.ClientSession() as session:
        headers = {
            "authority": "api.covalenthq.com",
            "sec-ch-ua": '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",  # noqa: E501
            "sec-ch-ua-mobile": "?0",
            "authorization": config.COVALENT_BEARER_TOKEN,
            "accept": "*/*",
            "origin": "https://www.covalenthq.com",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://www.covalenthq.com/",
            "accept-language": "en-US,en;q=0.9,ru;q=0.8,es;q=0.7",
        }
        async with session.get(
            "https://api.covalenthq.com/_/alchemist/alchemists/",
            headers=headers,
        ) as response:
            response_json = await response.json()
            return response_json["data"]["alchemists"]
