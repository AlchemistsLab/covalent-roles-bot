import json

import sentry_sdk
import gspread_asyncio
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials

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


class SheetsHelper:
    def __init__(self):
        with open("credentials.json") as f:
            keys = json.load(f)

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

        def get_creds():
            creds = ServiceAccountCredentials.from_json_keyfile_dict(keys, scope)
            return creds

        self.gc = gspread_asyncio.AsyncioGspreadClientManager(get_creds)

    async def init(self):
        agc = await self.gc.authorize()
        self.sh = await agc.open_by_key(config.GOOGLE_SHEETS_KEY)

    async def get_data(self):
        result = dict()

        ws: gspread_asyncio.AsyncioGspreadWorksheet
        for ws in await self.sh.worksheets():
            sheet_name = ws.title
            result[sheet_name] = await ws.get_all_records()

        return result
