"""Background asyncio runtime for Telethon inside the web (Flask) process.

The Flask app runs synchronously (flask_socketio threading mode), but Telethon
is async. We host a single dedicated event loop on a daemon thread so any part
of the web app can schedule a coroutine and block for its result from a normal
request handler.

This is started once from main.py (and lazily on first use as a fallback when
the app is imported without main.py, e.g. tests/manual runs). Starting twice is
a no-op.
"""

import asyncio
import threading

import personal_auth

_loop = None
_thread = None
_lock = threading.Lock()
_started = False


def _run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def start_runtime():
    """Start the background loop thread once and register it with personal_auth.

    Idempotent: safe to call from both main.py and lazy first-use.
    """
    global _loop, _thread, _started
    with _lock:
        if _started:
            return _loop
        loop = asyncio.new_event_loop()
        thread = threading.Thread(target=_run_loop, args=(loop,), name="tg-runtime", daemon=True)
        thread.start()
        _loop = loop
        _thread = thread
        _started = True
        # personal_auth uses this loop for the connect flow. There is no
        # python-telegram-bot Application in the web process, so app=None — the
        # bot-notification path in _complete_personal_auth is guarded by
        # `if _runtime_app`, so passing None simply skips it.
        personal_auth.set_personal_auth_runtime(loop, None)
        return loop


def get_loop():
    if not _started:
        start_runtime()
    return _loop


def run_coro(coro, timeout=60):
    """Schedule a coroutine on the background loop and block for its result."""
    loop = get_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result(timeout=timeout)
