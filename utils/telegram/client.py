import random
import asyncio
from pathlib import Path
from logging import getLogger, Logger
from typing import Any, Callable

from telethon import TelegramClient, utils
from telethon.tl.functions import channels, contacts, messages
from telethon.tl.types import InputPhoneContact, User, Channel
from telethon.errors import FloodWaitError, PeerFloodError

from ..miscellaneous import sleep
from ..loggers.colourprinter import colourprinter as colour
from.telethon_utils import parse_phone, clean_phone

_base_loger = getLogger('Telegram')

class PhoneDeslogError(Exception):
    def __init__(self, message=None, tip=None, fatal=True, phone=''):
        self.message = message or f"Session {phone} logged out"
        self.tip = tip or "If your session is still active on your app, you can recreate it"
        self.fatal = fatal
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} (Tip: {self.tip}, Fatal: {self.fatal})"


class Client(TelegramClient):

    def __init__(
        self,
        session: str | Path,
        api_id: str | int,
        api_hash: str,
        base_logger: Logger = _base_loger,
        delay: float = 0.25,
        tolerance_flood: int = 5,
        receive_updates: bool = False,
        **kwargs: Any
    ):
        self.phone = clean_phone(Path(session))
        self.delay = delay
        self.tolerance_flood = tolerance_flood
        self.flood_count = 0
        self.logger = getLogger(self.phone)
        self.logger.setLevel(base_logger.level)
        self.logger.handlers = list(base_logger.handlers)

        try:
            super().__init__(session, api_id, api_hash, receive_updates, **kwargs)
        except Exception as e:
            self.logger.error(f'Error in instance of Client {e}')
            raise e

        async def sleep(self, delay=None):
            if not delay:
                delay = self.delay
            return await sleep(delay)

        async def start(self, request_code=False, **kwargs):
            self.logger.debug(f'starting connect...')

            try:

                if request_code:
                    return await super().start(phone=self.phone, **kwargs)

                await super().connect()
                await self.sleep()

                me = await super().get_me()
                if me:
                    self.name = colour(utils.get_display_name(me), 'PINK')
                    self.logger.info(f'{self.name} connected successfully.')
                    await self.sleep()
                else:
                    await self.send_code_request(self.phone)
                    raise PhoneDeslogError(phone=self.phone)

            except Exception as e:
                self.logger.error(f'Error in start client: {e}')

    async def run_callback(self, callback: Callable[[TelegramClient], Any], **kwargs: Any):
        task = asyncio.create_task(callback(self, **kwargs))

        try:
            await self.run_until_disconnected()
        finally:
            task.cancel()


    async def handle_exception(self, e: Exception):

        if any (isinstance(e, error) for error in [asyncio.CancelledError, KeyboardInterrupt, asyncio.TimeoutError]):
            self.logger.warning(f'Shutting down client...: {e.__class__.__name__}')
            await self.disconnect()

        elif isinstance(e, FloodWaitError):
            self.flood_count+=1

            if self.flood_count >= self.tolerance_flood:
                self.logger.warning(f'Flood error...Shutting down client')
                await self.disconnect(ensure_close=True)
                return True

            self.logger.warning(f'Flood error...sleeping {e.seconds}')
            await self.sleep(e.seconds)

        elif isinstance(e, PeerFloodError):

            self.flood_count+=1

            if self.flood_count >= self.tolerance_flood:
                self.logger.warning(f'Spam Error...Shutting down client')
                await self.disconnect(ensure_close=True)
                return True

            await self.sleep()

    async def disconnect(self, ensure_close=False):
        try:
            if self.is_connected():
                await super().disconnect()
        except Exception as e:
            self.logger.error(f'Error in disconnect: {e}')
            if ensure_close:
                try:
                    self.session.close()
                except Exception as e:
                    self.logger.debug(f'Error in close session: {e}')
        finally:
            await self.sleep()

    async def add_user_to_channel(self, user: User, channel: Channel, delay: float|int =None) -> None:
        name_user =  colour(utils.get_display_name(user), 'CYAN')
        name_channel =  colour(utils.get_display_name(channel), 'MAGENTA')

        try:
            await self.add_contact(user)
            await self(channels.InviteToChannelRequest(channel, [user]))
            self.logger.info(f'Added {name_user} to {name_channel}!')

        except Exception as e:
            self.logger.error(f'Error in add {name_user} to {name_channel} : {e}')
            await self.handle_exception(e)
            raise e

        finally:
            await self.sleep(delay)

    async def add_contact(self, user: User):
        try:
            await self(contacts.ImportContactsRequest(
                [InputPhoneContact(
                    random.randrange(-2**63, 2**63),
                    user.phone if user.phone else '',
                    user.first_name if user.first_name else '',
                    user.last_name if user.last_name else ''
                )]
            ))
            self.logger.info(f'Success in add_contact')
        except Exception as e:
            self.logger.error(f'Error in add_contact: {e}')
        finally:
            await self.sleep()

    async def _join_channel(self, username_link: str) -> bool: 
        try:
            await self(channels.JoinChannelRequest(username_link))
        except Exception as e:
            self.logger.error(f'Error in join_channel {e}')
            await self.get_dialogs()
    
        chat = (await self(channels.GetChannelsRequest([username_link]))).chats[0]
        result = not chat.left and not chat.restricted
        if result:
            self.logger.info(f'Success join in {chat.id}')
        return result

    async def join_chat(self, invite_link: str) -> bool: 
        try:
            await self(messages.ImportChatInviteRequest(utils.parse_username(invite_link)[0]))
        except Exception as e:
            self.logger.error(f'Error in join_chat {e}')
            await self.get_dialogs()
    
        entity = await self.get_entity(invite_link)
        self.logger.info(f'Success join in {entity.id}')
        return entity

    async def join_channel(self, link: str) -> bool:
        """Join channel. Returns whether client joined or not."""
        try:
            username, is_invite = utils.parse_username(link)

            if is_invite:
                return await self.join_chat(link)
            else:
                return await self._join_channel(link)
        except Exception as e:
            self.logger.error(f'Error in join_channel {e}')
            return False
