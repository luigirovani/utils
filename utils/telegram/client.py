# Copyright (C) 2024 Luigi Augusto Rovani

import random
import asyncio
import os
import re
import string
from pathlib import Path
from logging import getLogger, Logger
from typing import Any, Callable, List, Tuple, Dict
from datetime import datetime

from telethon import TelegramClient, utils, errors, types as telethon_types
from telethon.tl.functions import channels, contacts, messages
from telethon.tl.functions.phone import GetGroupParticipantsRequest, GetGroupCallRequest
from telethon.tl.functions.users import GetFullUserRequest

from telethon.tl.types import (
    InputPhoneContact, ChannelParticipantsAdmins, 
    InputGroupCall, GroupCall,
    User, Channel, Chat,
    ChannelFull, ChatFull, UserFull
)


from telethon.errors import FloodWaitError, PeerFloodError, AuthKeyDuplicatedError, PhoneNumberBannedError as PhoneNumberBanned

from ..miscellaneous import sleep, convert_iter
from ..loggers.colourprinter import colourprinter as colour
from ..loggers.loggers import getChilder
from .exceptions import *
from .types import *
from.telethon_utils import parse_phone, clean_phone, clean_session

_base_loger = getLogger('Telegram')
DELAY = os.getenv('CLIENT_DELAY', 0.25)
DEFAULT_TIMEOUT_CONNECT = os.getenv('DEFAULT_TIMEOUT_CONNECT', 10)


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
        parse_session : bool = True,
        **kwargs: Any
    ):
        session_path = clean_session(session) if parse_session else Path(session)
        self.phone = session_path.stem
        self.name = self.phone
        self.delay = delay
        self.flood_count = 0
        self.limit_spam_flood = limit_spam_flood
        self.logger = getChilder(self.phone, base_logger)

        try:
            super().__init__(str(session_path), api_id, api_hash, receive_updates=receive_updates, **kwargs)
        except Exception as e:
            if 'database is locked' in str(e).lower():
                e = DatabaseLockedError()
            elif 'disk' in str(e).lower() or 'image' in str(e).lower():
                e = ImageDiskMalformedError()

            msg = e.msg if isinstance(e, ClientError) else  str(e)
            self.logger.error(f'Error in instance of Client {msg}')
            raise e


    async def _connect_coro(self, request_code, **kwargs):

        if not self.is_connected():
            await super().connect()

        if kwargs.get('bot_token'):
            await super().start(**kwargs)

        elif request_code:
            await super().start(phone=self.phone, **kwargs)


    async def start(self, request_code=False, timeout=DEFAULT_TIMEOUT_CONNECT, **kwargs):
        self.logger.debug(f'starting connect...')

        try:
            await asyncio.wait_for(self._connect_coro(request_code, **kwargs), timeout)
            await self.sleep()

            if me := await super().get_me():
                self.name = self.get_display(me, 'PINK')
                self.logger.info(f'{self.name} connected successfully.')
                await self.sleep()
                self.create_group_table()
            else:
                await self.send_code_request(self.phone)
                raise PhoneDeslogError(phone=self.phone)    

            return self

        except Exception as e:

            if isinstance(e, PhoneNumberBanned):
                e = PhoneNumberBannedError()
            elif isinstance(e, AuthKeyDuplicatedError):
                e = SessionHackedError()
            elif isinstance(e, asyncio.TimeoutError):
                e = TimeoutError

            msg = e.msg if isinstance(e, ClientError) else  str(e)
            self.logger.error(f'Error in start client: {msg}')
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


    async def sleep(self, delay=None):
        if not delay:
            delay = self.delay
        return await sleep(delay)


    async def fetch_admins(self, group: Channel|Chat, ids: bool = True) -> List[User|int]:
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

    async def add_user_to_channel(
        self, 
        user: User|str, 
        channel: Channel|Chat|str, 
        delay: float|int|None =None, 
        join_channel: bool = True,
        fwd_limit: int = 100,
        stack_info: bool = False,
    ) -> None:

        if isinstance(channel, str):
            channel = await self.join_channel(channel) if join_channel else await self.get_input_entity(channel)

        name_user =  self.get_display(user, 'CYAN')
        name_channel = self.get_display(channel, 'MAGENTA')

        try:

            if isinstance(channel, Chat):
                await self(messages.AddChatUserRequest(channel.id, user, fwd_limit))
            else:
                await self(channels.InviteToChannelRequest(channel, [user]))

            self.logger.info(f'Added {name_user} to {name_channel}!')

        except Exception as e:
            self.logger.error(f'Error in add {name_user} to {name_channel}: {e.__class__.__name__}', stack_info=stack_info)
            raise e

        finally:
            await self.sleep(delay)

    async def add_contact(self, user: User, raise_exceptions: bool = False) -> bool:
        try:
            if user.phone:

                await self(contacts.ImportContactsRequest(InputPhoneContact(
                    random.randrange(-2**63, 2**63),
                    user.phone,
                    user.first_name if user.first_name else '',
                    user.last_name if user.last_name else ''
                )))

                await self(contacts.SearchRequest(
                    q=user.phone,
                    limit=100
                ))
                await self.sleep()
                self.logger.debug(f'Success in add_contact')
                return True

        except Exception as e:
            self.logger.debug(f'Error in add_contact: {e}')
            if raise_exceptions:
                raise e

        finally:
            await self(contacts.SearchRequest(
                q=utils.get_display_name(user),
                limit=100
            ))
            await self.sleep()

    async def search_groups(self, key: str, limit: int = 100):
        try:
            results = await self(contacts.SearchRequest(
                q=key,
                limit=limit
            ))
            return results
        except Exception as e:
            await self.logger.debug(f'Error in search_groups: {e}')
            return []
        finally:
            await sleep()

    async def resolve_username(self, username: str) -> User|None:
        try:
            result = await self(contacts.ResolveUsernameRequest(username))
            return result.users[0]

        except Exception as e:
            self.logger.debug(f'Error in resolve_username: {e}')

    async def _resolve_user_entity(self, entity: User):

        try:
            return await self.resolve_username(entity.username)
        except:
            pass

        try:
            await self.add_contact(entity, raise_exceptions=True)
            return await self._get_entity_from_string(entity.phone)
        except:
            pass

        try:
            return await self.get_input_entity(entity)
        except:
            pass

    async def resolve_user_entity(self, entity: User, msg: str = 'oi') -> User|None:
        if result := await self._resolve_user_entity(entity):
            return result

        try:
            await self.send_message(entity, msg)
        except:
            pass

    async def view_message(self, chat_id: int|str|GroupType, msg_id: List[int]|int, increment: bool = True, raise_exceptions: bool = False):
        try:
            await self(messages.GetMessagesViewsRequest(
                peer=chat_id,
                id=convert_iter(msg_id),
                increment=increment
            ))
        except Exception as e:
            if raise_exceptions:
                raise e
            self.logger.debug(f'Error in view_message: {e}')

    async def react_message(
        self, 
        chat_id: int|str|GroupType, 
        msg_id: int, 
        emoji: str, 
        view: bool = True, 
        big: bool = True, 
        add_to_recent: bool = True, 
        delay: float|int = None,
        prob: float = 1.0
    ):
        if view:
            await self.view_message(chat_id, msg_id, increment=True)
            await self.sleep(delay)

        try:         
            if random.random() < prob: 
                await self(messages.SendReactionRequest(
                    peer=chat_id,
                    msg_id=chat_id,
                    big=big,
                    add_to_recent=add_to_recent,
                    reaction=[telethon_types.ReactionEmoji(
                        emoticon=emoji
                    )]
                ))
                await sleep(delay)

        except Exception as e:
            self.logger.error(f'Error in react_message: {e}')


    async def get_full_entity(self, entity: Channel|Chat|User|str|int) -> ChatFull|ChannelFull|UserFull:

        if isinstance(entity, ChannelType):
            return (await self(channels.GetFullChannelRequest(entity))).full_chat
        elif isinstance(entity, ChannelType):
            return (await self(messages.GetFullChatRequest(entity))).full_chat
        elif isinstance(entity, UserType):
            return (await self(GetFullUserRequest(entity))).full_user
        else:
            raise TypeError('Invalid group type')

    async def get_call(self, group: GroupType, limit: int = 100, complete_entity: bool = False) -> InputGroupCall|GroupCall|None:
        full_chat = await self.get_full_entity(group)

        if hasattr(full_chat, 'call') and full_chat.call:
            result = await self(GetGroupCallRequest(full_chat.call, limit))
            if complete_entity:
                return result

            call = full_chat.call
            call.active = not bool(result.call.schedule_date)
            return call

    async def fetch_participants_from_call(
        self,
        call: InputGroupCall,
        group: GroupType, 
        max_requests: int = 20, 
        limit: int  = 100
    )-> List[User]:

        users = []
        offset = ''

        for _ in range (max_requests):
            result = await self(GetGroupParticipantsRequest(
                call=call,
                ids=[],
                sources=[],
                offset=offset,
                limit=limit
            ))

            self.session.process_entities(result)
            self.session.save()

            for participant in result.users:
                users.append(participant)

            if len(users) >= result.count-2:
                break 

            offset = result.next_offset
            await self.sleep()

        self.logger.info(f'Fetched {len(users)} participants from {self.get_display(group)}')
        return users


    async def fetch_users_from_reply(self, channel: Channel, limit: int = 20, delay: int|float = None) -> List[User]:
        users = {}

        async for message in self.iter_messages(channel, limit=limit):
            if hasattr(message, 'replies') and message.replies and message.replies.replies > 0:
                reply = await self(messages.GetRepliesRequest(
                    peer=channel,
                    msg_id=message.id,
                    offset_id=0,  
                    offset_date=None,
                    add_offset=0,
                    limit=100,  
                    max_id=0,
                    min_id=0,
                    hash=0                            
                ))
                for user in reply.users:
                    users[user.id] = user

                await self.sleep(delay)

        return list (users.values())

    async def fetch_all_participans(self, channel: Channel, delay: int|float = None) -> List[User]:
        pattern = re.compile(r"\b[a-zA-Z]")
        users = []
    
        for key in list(string.ascii_lowercase):
            offset, limit = 0, 199
            while True:
                participants = await  self(
                    channels.GetParticipantsRequest(
                        channel, telethon_types.ChannelParticipantsSearch(key), offset, limit, hash=0
                    )
                )
                if not participants.users:
                    break

                for participant in participants.users:
                    try:
                        if pattern.findall(participant.first_name)[0].lower() == key:
                            users.append(participant)
                    except:
                        pass
                        
                offset += len(participants.users)
                await self.sleep(delay)

        return users

    async def check_spambot(self) -> Tuple[bool, datetime|None]:
        spambot = 'SpamBot'
        datepattern = re.compile(r"(\d{1,2} \w+ \d{4}, \d{2}:\d{2} UTC)")
        spamtext = [
            "no limits are currently applied to your account",
            "nenhum limite foi aplicado"
        ]

        try:
            await self.send_message(spambot, '/start')
            await self.sleep(2)
            msg = await self.get_messages(spambot, limit=1)
            msg = msg[0].text

            if any (text in msg for text in spamtext):
                self.logger.debug(f'Client is not a spambot')
                return False, None

                     
            if matches := datepattern.findall(msg):
                for match in matches:
                    date_limitation = datetime.strptime(match, '%d %b %Y, %H:%M %Z')
                    self.logger.debug(f'Client is a spambot until {date_limitation}')
                    return True, date_limitation

            return False, None

        except Exception as e:
            if 'blocked this user' in str(e).lower():
                self.logger.debug(f'Client blocked spambot\n Try again ')
                return False, None
            self.logger.error(f'Error in check_spambot: {e}')

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


    async def check_group(self, entity: EntityLike, check_add=False) -> None|Chat|Channel:
        entity = await self.get_entity(entity)

        if any ([
            isinstance(entity, BannedGroupType),
            isinstance(entity, Channel) and (entity.restricted and entity.banned_rights.view_messages),
            isinstance(entity, GroupEntity) and entity.left
        ]):
            raise ValueError(f'Kicked in {self.get_display(entity)}!')

        if check_add and entity.default_banned_rights.invite_users:
            self.logger.error(f'Not permission to add in {self.get_display(entity)}!')
            return None

        return entity

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

    async def join_chat(self, acess_hash: str, second_try=False) -> None:

        try:
            await self(messages.ImportChatInviteRequest(acess_hash))
            
        except errors.ChannelsTooMuchError:
            self.logger.warning(f'ChannelsTooMuchError')
            if not second_try:
                await self.leave_channels()
                return await self.join_chat(acess_hash, True)

        except errors.UserAlreadyParticipantError:
            pass
        except errors.InviteRequestSentError as e:
            self.logger.warning(f'Client awaiting approval to chat')
            if not second_try:
                await self.sleep(3)
                return await self.join_chat(acess_hash, True)
            raise e

        except Exception as e:
            self.logger.error(f'Error in join_chat {e}')    

    async def join_channel(self, link: str) -> Channel|Chat|None:
        """Join channel or chat. Return entity or None"""
        entity = None

        try:
            entity = await self.get_input_entity(link)
            info_group, retry = self.check_joined(entity, link)

            if info_group:
                self.logger.debug(f'client already part of group {self.get_display(entity)}!')
                return entity

            if not retry:
                self.logger.debug(f'Error in join_channel {link}')
                return None
             
            acess_hash, is_invite = utils.parse_username(link)
            if is_invite:
                await self.join_chat(acess_hash)
            else:
                await self._join_channel(link)
            
            entity = await self.check_group(link)
            self.logger.info(f'Success join in {self.get_display(entity, 'LC')}')
            self.add_joined_group(entity.id, link)
            return entity

        except Exception as e:
            self.logger.error(f'Error in join_channel {e}')
            self.add_error_join_group(entity, link)

    async def join_group(self, link: str) -> Channel|Chat|None:
        return await self.join_channel(link)

    @staticmethod
    def colour(text: str, color: str) -> str:
        return colour(text, color)

    @staticmethod
    def get_id(entity) -> int:
        try:
            peer_id = utils.get_peer_id(entity)
            return peer_id if peer_id else 0
        except:
            return 0

    def get_display(self, entity, color: str = 'LM') -> str:

        if isinstance(entity, dict) and entity.get('name'):
            display_name = entity['name']
        else:
            display_name = utils.get_display_name(entity)

        if not display_name:

            if cached_entity := self.get_cached_entity(entity):
                display_name = cached_entity['name']

            elif group := self.get_group_info(entity):
                display_name = group['name']

            elif isinstance(entity, (str, int)):
                display_name = str(entity)
            else:
                display_name = ''

        return colour(display_name, color)

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

    def get_cached_entity(self, entity, resolve = False) -> Dict[str, Any]| None:

        if resolve:
            try:
                username, is_invite = utils.parse_username(entity)
                if username and not is_invite:
                    entity = username
                return self.session.get_input_entity(entity)
            except:
                pass

        query = 'SELECT * FROM entities WHERE id = ?'
        if entity_id := self.get_id(entity):
            result = self.get_query(query, (entity_id,), to_dict=True)
            return result[0] if result else None

    def get_query(self, query: str, data: Tuple = (), to_dict: bool = False) -> List[Tuple[Any]|Dict[str,Any]]:
        c = self.session._cursor()
        c.execute(query, data)
        result = c.fetchall()

        if to_dict and result:
            column_names = [col[0] for col in c.description]
            result = [
                dict(zip(column_names, row))
                for row in result
            ]

        c.close()
        return result

    def execute_query(self, query: str, data: Tuple = ()) -> None:
        c = self.session._cursor()
        try:
            c.execute(query, data)
        except Exception as e:
            print(e)
        self.session.save()
        c.close()

    def create_group_table(self):
        self.execute_query("""
            BEGIN;
            DROP TABLE IF EXISTS groups_temp;
            CREATE TABLE groups_temp (
                id INTEGER PRIMARY KEY, 
                link TEXT UNIQUE,
                name TEXT,
                broadcast INTEGER DEFAULT 0,
                raised_errors INTEGER DEFAULT 0,
                joined INTEGER DEFAULT 0
            );
            -- Verifica se a tabela 'groups' existe e sua estrutura
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY, 
                link TEXT UNIQUE,
                name TEXT,
                broadcast INTEGER DEFAULT 0,
                raised_errors INTEGER DEFAULT 0,
                joined INTEGER DEFAULT 0
            );
            INSERT INTO groups SELECT id, link, raised_errors, joined FROM groups_temp
            ON CONFLICT.. Existing.
        END
        """)

    def add_joined_group(self, group: Chat|Channel, link: str):
        group_id = self.get_id(group)
        name = utils.get_display_name(group)
        broadcast = 1 if isinstance(group, Channel) and group.broadcast else 0
        data = (group_id, link, name, broadcast, 0, 1)
        query = """
            INSERT INTO groups (id, link, name, broadcast, raised_errors, joined)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                link = excluded.link,
                name = excluded.name,
                broadcast = excluded.type,
                raised_errors = excluded.raised_errors,
                joined = excluded.joined;
        """
        self.execute_query(query, data)

    def check_joined(self, group: GroupType, link: str) -> Tuple[bool|Dict, bool]:
        group_id = self.get_id(group)
        query = 'SELECT *  FROM groups WHERE id = ? OR link = ?'

        if result := self.get_query(query, (group_id, link), to_dict=True):
            return result if result[0]['joined'] else False, result[0]['raised_errors']  < 4

        return False, False

    def add_error_join_group(self, group: GroupType, link: str):
        group_id = self.get_id(group)

        if group_id:
            query = """
                INSERT INTO groups (id, link, joined)
                VALUES (?, ?, ?)
                ON CONFLICT(link) DO UPDATE SET
                    id = excluded.id,
                    joined = excluded.joined;
                ON CONFLICT(id) DO UPDATE SET
                    joined = excluded.joined;
                DO UPDATE SET
                    raised_errors = raised_errors + 1
            """
            data = (group_id, link, 1)
        else:
            query = """
                INSERT INTO groups (link, joined)
                VALUES (?, ?)
                ON CONFLICT(link) DO UPDATE SET
                    joined = excluded.joined;
                DO UPDATE SET
                    raised_errors = raised_errors + 1
            """
            data = (link, 1)

        self.execute_query(query, data)

        query = 'SELECT raised_errors FROM groups WHERE id = ? OR link = ?'
        if result := self.get_query(query, (group_id, link), to_dict=True):
            raised_errors = result[0]['raised_errors'] + 1
            query = 'UPDATE groups SET raised_errors = ? WHERE id = ? OR link = ?'
            self.execute_query(query, (raised_errors, group_id, link))

    def get_group_info(self, group: GroupType):
        if group_id := self.get_id(group):
            if result := self.get_query('SELECT * FROM groups WHERE joined = 1 and id = ?', (group_id,)):
                return result[0]
