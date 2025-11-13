# asgi_probe.py
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route

async def probe(request):
    return PlainTextResponse("asgi-ok", status_code=200)

application = Starlette(routes=[Route("/_probe", probe)])
