from ast import Tuple
import asyncio
from pathlib import Path
import random
from typing import Callable, Any, Union, Tuple, List
from logging import Logger, getLogger

from telethon import TelegramClient, utils

from.sessions import get_sessions_phones
from.telethon_utils import is_list_like
from..files import read_csv
from..miscellaneous import sleep

_base_loger = getLogger('Telegram')

async def run_client(
    session: Union[str, Path],
    phone: str,
    api_id: Union[str, int],
    api_hash: str,
    callback: Callable[[TelegramClient], Any],
    base_logger: Logger = _base_loger,
    delay_connect: float = 0.25,
    receive_updates: bool = False,
    **keyargs: Any
) -> None:
    """
    Runs the Telegram client and executes the callback function.

    Args:
        session (str): The session string or path to the session file.
        phone (str): The phone number associated with the session.
        api_id (int): The API ID for the Telegram client.
        api_hash (str): The API hash for the Telegram client.
        callback (Callable[[TelegramClient], Any]): The function to execute with the client.
        base_logger (Any): The base logger for logging.
        delay_connect (float): The delay in seconds before connecting.
        receive_updates (bool): Whether to receive updates in the session.
        **keyargs (Any): Additional arguments for the Telegram client.

    Returns:
        None
    """
    client: TelegramClient | None = None
    logger = base_logger.getChild(phone)

    try:
        client = TelegramClient(session, api_id, api_hash, receive_updates=receive_updates, **keyargs)
        await client.connect()
        await sleep(delay_connect)
        client.logger = logger

        try:
            me = await client.get_me()
            if me:
                logger.info(f'{utils.get_display_name(me)} connected successfully.')
                try:
                    await callback(client)
                except KeyboardInterrupt as e:
                    logger.debug('Terminating program! Please wait...')
                    raise e
                except Exception as e:
                    logger.error(f'Error executing {callback.__name__}: {e}')
            else:
                logger.warning('Session is logged out or banned.')

        finally:
            try:
                await client.disconnect()
            except Exception as e:
                logger.debug(f'Error during disconnect: {e}')

    except Exception as e:
        logger.error(f'Error connecting: {e}')

def get_api(
    api: Union[Tuple[str, str], Tuple[int, str], Path, str]
) -> List[Tuple[int, str]]:
    """
    Returns the API ID and API hash from the given API.

    Args:
        api (Union[Tuple[str, str], Tuple[int, str], Path, str]): The API ID and API hash.

    Returns:
        List[Tuple(int, str)]: The API ID and API hash.
    """
    if isinstance(api, Path) or isinstance(api, str):
        return read_csv(api, drop=True, skip_header=True)

    if is_list_like(api):
        if is_list_like(api[0]):
            return api
        return [tuple(api)]

    raise ValueError('Invalid API format.')

async def run_task(task, sem, delay_task, *args, **keyargs):
    async with sem:
        await sleep(delay_task)
        return await task(*args, **keyargs)

async def run_app(
    sessions_path,
    api: Union[Tuple[str, str], Tuple[int, str], Path, str],
    callback: Callable[[TelegramClient], Any],
    max_tasks: int = 12,
    delay_task: float = 1,
    base_logger: Logger = _base_loger,
    delay_connect: float = 0.25,
    receive_updates: bool = False,
    **keyargs
):
    """
    Runs the Telegram client for each session in the given path.

    Args:
        sessions_path (str): The path to the sessions.
        api (Union[Tuple[str, str], Tuple[int, str], Path, str]): The API ID and API hash.
        callback (Callable[[TelegramClient], Any]): The function to execute with the client.
        max_tasks (int): The maximum number of tasks to run concurrently.
        base_logger (Logger): The base logger for logging.
        delay_connect (float): The delay in seconds before connecting.
        receive_updates (bool): Whether to receive updates in the session.

    Returns:
        None
    """
    apis = get_api(api)
    sessions = get_sessions_phones(sessions_path)
    sem = asyncio.Semaphore(max_tasks)
    tasks = []

    for phone, session in sessions:
        api_id, api_hash = random.choice(apis)

        tasks.append(asyncio.create_task(run_task(
            run_client, sem, delay_task,
            session=session, phone=phone,
            api_id=api_id, api_hash=api_hash, 
            callback=callback, base_logger=base_logger,
            delay_connect=delay_connect, 
            receive_updates=receive_updates, **keyargs
        )))

    await asyncio.gather(*tasks)












