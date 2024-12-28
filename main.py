from miscellaneous.async_utils import Runner, sleep
import asyncio

async def task(runner: Runner):
    print('Task started')
    await sleep(1)
    runner.finish('Task finished')

async def run():
    runner = Runner()
    for i in range (5):
        runner.push(task(runner))
    await runner

asyncio.run(run())




