import logging
import os
from asyncio import CancelledError, create_subprocess_exec, sleep, subprocess

import aiofiles
from aiohttp import web

# noinspection PyArgumentList
logging.basicConfig(
    level=logging.DEBUG,
    format='{asctime} - {name} - {levelname} - {message}',
    style='{',
)
logger = logging.getLogger('server')


async def get_index(request):
    async with aiofiles.open('templates/index.html') as file:
        html = await file.read()
    return web.Response(text=html, content_type='text/html')


async def make_archive(request):
    name = request.match_info['name']
    dir_path = os.path.join(request.app.static_dir, name)
    if not os.path.exists(dir_path):
        logger.warning(f'Directory {dir_path} not found.')
        raise web.HTTPNotFound(reason='Directory not found :(')

    response = web.StreamResponse()
    response.headers.update({
        'Content-Type': 'text/html',
        'Transfer-Encoding': 'chunked',
        'Content-Disposition': f'attachment; filename="{name}.zip"'
    })
    await response.prepare(request)

    proc = await create_subprocess_exec(
        'zip', '-r', '-', name,
        cwd=request.app.static_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        while not proc.stdout.at_eof():
            chunk = await proc.stdout.read(1024 * 10)
            logger.debug(f'Send {len(chunk)} bytes chunk.')
            await response.write(chunk)
            await sleep(app.delay)
    except CancelledError as error:
        logger.debug('Cancelled error.')
        proc.terminate()
        raise CancelledError from error
    return response


if __name__ == '__main__':
    app = web.Application()
    app.static_dir = 'photos'
    app.delay = 1
    app.add_routes([
        web.get('/', get_index),
        web.get('/download/{name}/', make_archive),
        web.static('/static', app.static_dir),
    ])
    web.run_app(app)
