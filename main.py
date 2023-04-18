from aiohttp import web
from route import web_server
from pyrogram import Client, __version__
from configs import API_ID, API_HASH, BOT_TOKEN, LOGGER, PORT

class FilterBot(Client):

    def __init__(self):
        super().__init__(
         name="FilterBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, plugins={"root": "FilterBot"}, workers=50, sleep_threshold=5,
        )
        self.LOGGER = LOGGER

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.LOGGER(__name__).info(f"{me.first_name} with for Pyrogram v{__version__} started on {me.username}.")

        app = web.AppRunner(await web_server())
        await app.setup()       
        await web.TCPSite(app, "0.0.0.0", PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped. Bye.")

FilterBot().run()
