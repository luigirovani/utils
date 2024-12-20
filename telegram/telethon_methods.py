from ast import Tuple
import asyncio
from pathlib import Path
import random
from typing import Callable, Any, Union, Tuple, List
from logging import Logger, getLogger
from venv import logger

from.sessions import get_sessions_phones
from.client import Client, DELAY
from..miscellaneous import sleep, is_list_like
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
        async with Client(session, api_id, api_hash, base_logger, delay, receive_updates=receive_updates, cancelled_event=cancelled_event **keyargs) as client:
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

    sem = asyncio.Semaphore(max_tasks)
    cancelled_event = asyncio.get_event_loop().create_future()
    tasks = []

    for phone, session in sessions:
        api_choice = random.choice(apis)

        tasks.append(asyncio.create_task(run_task(
            run_client, sem, delay_task,
            session=session, phone=phone,
            api_id=api_choice[0], api_hash=api_choice[1], 
            callback=callback, base_logger=base_logger,
            delay=delay, cancelled_event=cancelled_event,
            receive_updates=receive_updates, **keyargs
        )))

    task = asyncio.gather(*tasks, return_exceptions=True)

    def on_task_done(finished_task: asyncio.Future):
        if not task.done():
            task.cancel()

        if finished_task.done():
            try:
                if result := finished_task.result():
                    base_logger.info(f'{callback.__name__} Finished: {result}')
            except asyncio.CancelledError:
                base_logger.warning(f'{callback.__name__} Cancelled')
                pass
            except Exception as e:
                base_logger.critical(f'{callback.__name__} Error : {e}')

    cancelled_event.add_done_callback(on_task_done)
    await task
    if not cancelled_event.done():
        cancelled_event.set_result('')
    await cancelled_event
    












