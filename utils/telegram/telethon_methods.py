import asyncio
from pathlib import Path
import random
from typing import Callable, Any, Union, Tuple, List
from logging import Logger, getLogger

from.sessions import get_sessions_phones
from.client import Client, DELAY
from..miscellaneous import sleep, is_list_like, Runner
from..files import read_csv

_base_loger = getLogger('Telegram')


async def run_client(
    session: Union[str, Path],
    phone: str,
    api_id: Union[str, int],
    api_hash: str,
    callback: Callable[[Client], Any],
    base_logger: Logger = _base_loger,
    delay: float = DELAY,
    receive_updates: bool = False,
    cancelled_event=None,
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
        delay (float): The delay in seconds before connecting.
        receive_updates (bool): Whether to receive updates in the session.
        **keyargs (Any): Additional arguments for the callback client.

    Returns:
        None
    """

    try:
        async with Client(session, api_id, api_hash, base_logger, delay, receive_updates=receive_updates, cancelled_event=cancelled_event, **keyargs) as client:
            await callback(client)

    except (KeyboardInterrupt, asyncio.CancelledError):
        raise 

    except Exception as e:
        base_logger.error(f'Error connecting {phone} : {e}')

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
        apis = read_csv(api, drop=True, skip_header=True)
        return [(peer[0], peer[1]) for peer in apis]

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
    callback: Callable[[Client], Any],
    max_tasks: int = 12,
    delay_task: float = 1,
    limit_sessions: int = None,
    base_logger: Logger = _base_loger,
    delay: float = DELAY,
    receive_updates: bool = False,
    black_list_phones: List[str] = [],
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
        delay (float): The delay in seconds before connecting.
        receive_updates (bool): Whether to receive updates in the session.

    Returns:
        None
    """
    apis = get_api(api)
    sessions = [s for s in get_sessions_phones(sessions_path) if s not in black_list_phones]
    random.shuffle(sessions)
    if limit_sessions:
        sessions = sessions[:limit_sessions]

    runner = Runner(name='app', logger=base_logger, max_tasks=max_tasks, delay=delay_task)

    for phone, session in sessions:
        api_choice = random.choice(apis)

        runner.push(run_client(
            session=session, phone=phone,
            api_id=api_choice[0], api_hash=api_choice[1], 
            callback=callback, base_logger=base_logger,
            delay=delay, cancelled_event=runner,
            receive_updates=receive_updates, **keyargs
        ))

    await runner.run()












