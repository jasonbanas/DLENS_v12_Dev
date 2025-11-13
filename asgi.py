from asgiref.wsgi import WsgiToAsgi
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route, Mount

# Pure-ASGI probe (never fails)
async def probe(request):
    return PlainTextResponse("asgi-ok", status_code=200)

def mount_flask_asgi():
    try:
        # Import Flask app lazily so errors are caught and surfaced
        from api.app import app as flask_app
        return WsgiToAsgi(flask_app), None
    except Exception as e:
        # Return a tiny ASGI app that always 500s with the import error text
        async def failing_app(scope, receive, send, err=e):
            msg = f"Flask import failed:\n{err.__class__.__name__}: {err}"
            resp = PlainTextResponse(msg, status_code=500)
            await resp(scope, receive, send)
        return failing_app, e

flask_asgi, _err = mount_flask_asgi()

application = Starlette(
    routes=[
        Route("/_probe", probe),
        # Mount Flask (or the error shim) at /
        Mount("/", app=flask_asgi),
    ]
)
