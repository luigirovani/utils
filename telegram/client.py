import random
import asyncio
import os
from pathlib import Path
from logging import getLogger, Logger
from typing import Any, Callable

from telethon import TelegramClient, utils, errors
from telethon.tl.functions import channels, contacts, messages
from telethon.tl.types import InputPhoneContact, User, Channel, Chat, ChannelParticipantsAdmins
from telethon.errors import FloodWaitError, PeerFloodError


from ..miscellaneous import sleep
from ..loggers.colourprinter import colourprinter as colour
from ..loggers.loggers import getChilder
from.telethon_utils import parse_phone, clean_phone, clean_session

_base_loger = getLogger('Telegram')
DELAY = os.getenv('CLIENT_DELAY', 0.25)

class PhoneDeslogError(Exception):
    def __init__(self, message=None, phone=''):
        self.message = message or f"Session {phone} logged out"
        super().__init__(self.message)


class Client(TelegramClient):

    def __init__(
        self,
        session: str | Path,
        api_id: str | int,
        api_hash: str,
        base_logger: Logger = _base_loger,
        delay: float = DELAY,
        receive_updates: bool = False,
        limit_spam_flood: int = 5,
        **kwargs: Any
    ):
        session_path = clean_session(session)
        self.phone = session_path.stem
        self.name = self.phone
        self.delay = delay
        self.flood_count = 0
        self.limit_spam_flood = limit_spam_flood
        self.logger = getChilder(self.phone, base_logger)

        try:
            super().__init__(session_path, api_id, api_hash, receive_updates=receive_updates, **kwargs)
        except Exception as e:
            self.logger.error(f'Error in instance of Client {e}')
            raise e

    async def start(self, request_code=False, **kwargs):
        self.logger.debug(f'starting connect...')

        try:
            if not self.is_connected():
                await super().connect()
                await self.sleep()

            if request_code:
                return await super().start(phone=self.phone, **kwargs)

            me = await super().get_me()
            if me:
                self.name = colour(utils.get_display_name(me), 'PINK')
                self.logger.info(f'{self.name} connected successfully.')
                await self.sleep()
                self.create_group_table()
            else:
                await self.send_code_request(self.phone)
                raise PhoneDeslogError(phone=self.phone)

            return self

        except Exception as e:
            self.logger.error(f'Error in start client: {e}')
            raise e

    async def disconnect(self, ensure_close=False):
        self.logger.debug(f'Starting disconnect')

        try:
            await super().disconnect()
            self.logger.info(f'{self.name} disconnected successfully.')

        except Exception as e:
            self.logger.warning(f'Error in disconnect: {e}')

        if ensure_close:
            try:
                self.session.close()
            except Exception as e:
                self.logger.debug(f'Error in close session: {e}')

    async def run_callback(self, callback: Callable[[TelegramClient], Any], timeout=None, **kwargs: Any):
        c_name = colour(callback.__name__, 'Y')
        self.logger.debug(f'Starting {c_name}...')

        try:
            return await asyncio.wait_for(callback(self, **kwargs), timeout=timeout)

        except (asyncio.CancelledError, KeyboardInterrupt) as e:
            self.logger.warning(f'Shutting down app {c_name} Error: {e.__class__.__name__}')
            raise e
        except Exception as e:
            self.logger.error(f'Error in run {c_name}: {e}')

    async def handle_exception(self, e: Exception) -> bool:

        if isinstance(e, FloodWaitError):
            self.flood_count+=1

            if self.flood_count >= self.limit_spam_flood:
                self.logger.warning(f'Client has reached the flood limit.')
                return True

            self.logger.warning(f'Flood error...sleeping {e.seconds}')
            await self.sleep(e.seconds)

        elif isinstance(e, PeerFloodError):
            self.flood_count+=1

            if self.flood_count >= self.limit_spam_flood:
                self.logger.warning(f'Client has reached the Spam limit.')
                return True

            await self.sleep()

        return False

    def create_group_table(self):
        c = self.session._cursor()
        c.execute('CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY, joined INTEGER DEFAULT 0)')
        c.close()
        self.session.save()

    def add_joined_group(self, group_id: int):
        c = self.session._cursor()
        c.execute('INSERT OR IGNORE INTO groups (id, joined) VALUES (?, 1)', (group_id,))
        c.close()
        self.session.save()

    def get_joined_groups(self):
        c = self.session._cursor()
        c.execute('SELECT id FROM groups WHERE joined = 1')
        result = c.fetchall()
        c.close()
        return result

    def remove_joined_group(self, group_id: int):
        c = self.session._cursor()
        c.execute('DELETE FROM groups WHERE id = ?', (group_id,))
        c.close()
        self.session.save()

    async def sleep(self, delay=None):
        if not delay:
            delay = self.delay
        return await sleep(delay)

    @staticmethod
    def colour(text: str, color: str) -> str:
        return colour(text, color)

    @staticmethod
    def get_display(entity: User|Channel|Chat, color: str = 'LM') -> str:
        return colour(utils.get_display_name(entity), color)

    @staticmethod
    def parse_phone(phone: str|int) -> str:
        return parse_phone(phone)

    @staticmethod
    def clean_phone(phone: str|int|Path) -> str:
        return clean_phone(phone)

    @staticmethod
    def clean_session(session_path: str|Path) -> Path:
        return clean_session(session_path)

    @staticmethod
    def is_entity(obj: Any) -> bool:
        return isinstance(obj, (User, Channel, Chat))


    async def fetch_admins(self, group: Channel|Chat, ids: bool = True) -> list[User|int]:
        users = []

        try:
            async for user in self.iter_participants(group, filter=ChannelParticipantsAdmins):
                users.append(user)

            if not users:
                users = [user async for user in self.iter_participants(group)]
                if len (users) > 40:
                    users = []

            self.logger.debug(f'Fetched {len(users)} admins from {self.get_display(group)}')

        except Exception as e:
            self.logger.error(f'Error in fetch_admins: {e}')

        return [user.id for user in users] if ids else users

    async def add_user_to_channel(self, user: User, channel: Channel|Chat, delay: float|int =None, add_contat: bool = True) -> None:
        name_user =  colour(user.first_name, 'CYAN')
        name_channel =  colour(utils.get_display_name(channel), 'MAGENTA')

        try:
            if add_contat:
                await self.add_contact(user)

            if isinstance(channel, Chat):
                await self(messages.AddChatUserRequest(channel.id, user.id, 100))
            else:
                await self(channels.InviteToChannelRequest(channel, [user]))

            self.logger.info(f'Added {name_user} to {name_channel}!')

        except Exception as e:
            self.logger.error(f'Error in add {name_user} to {name_channel}: {e.__class__.__name__}')
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
            self.logger.debug(f'Success in add_contact')
        except Exception as e:
            self.logger.debug(f'Error in add_contact: {e}')
        finally:
            await self.sleep()

    async def leave_channels(self, limit: int = 5):
        count = 1
        self.logger.debug(f'Leaving channels...')
        joined_groups = [int(group[0]) for group in self.get_joined_groups()]

        async for dialog in self.iter_dialogs():
            try:
                if not dialog.is_channel:
                    continue
                
                entity = await self.get_entity(dialog.entity)
                if entity.id  in joined_groups:
                    continue

                count+=1
                result = await self(channels.LeaveChannelRequest(channel=entity))
                self.logger.debug(f'leave sucess channel {result.chats[0].title}')

            except FloodWaitError:
                break
            except Exception as e:
                self.logger.debug(f'Error in leave channel: {e}')

            if count >= limit:
                break

    async def _join_channel(self, username_link: str, second_try=False) -> None: 
        try:
            await self(channels.JoinChannelRequest(username_link))

        except errors.ChannelsTooMuchError:
            self.logger.warning(f'ChannelsTooMuchError')
            if not second_try:
                await self.leave_channels()
                return await self._join_channel(username_link, True)

        except Exception as e:
            self.logger.error(f'Error in join_channel {e}')
            await self.get_dialogs()
    
        chat = (await self(channels.GetChannelsRequest([username_link]))).chats[0]
        if chat.left or chat.restricted:
            raise ValueError(f'Kicked in {self.get_display(chat)}!')

    async def join_chat(self, acess_hash: str, second_try=False) -> None:

        try:
            await self(messages.ImportChatInviteRequest(acess_hash))
            
        except errors.ChannelsTooMuchError:
            self.logger.warning(f'ChannelsTooMuchError')
            if not second_try:
                await self.leave_channels()
                return await self.join_chat(acess_hash, True)
        except (errors.UserAlreadyParticipantError, errors.InviteRequestSentError):
            pass
        except Exception as e:
            self.logger.error(f'Error in join_chat {e}')
            await self.get_dialogs()
    

    async def join_channel(self, link: str) -> Channel|Chat|None:
        """Join channel or chat. Return entity or None"""

        try:
            try:
                entity = await self.get_entity(link)
                ids = [g[0] for g in self.get_joined_groups()]
                if entity.id in ids:
                    return entity
            except:
                entity = None
             
            acess_hash, is_invite = utils.parse_username(link)
            if is_invite:
                await self.join_chat(acess_hash)
            else:
                await self._join_channel(link)

            entity = await self.get_entity(link)
            self.logger.info(f'Success join in {self.get_display(entity, 'LC')}')
            self.add_joined_group(entity.id)
            return entity

        except Exception as e:
            self.logger.error(f'Error in join_channel {e}')
            if entity:
                self.remove_joined_group(entity.id)
