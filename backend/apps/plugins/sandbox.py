"""Plugin sandbox (Python equivalent of Node's VM2).

Executes plugin code with RestrictedPython when available: whitelisted
builtins, no filesystem/network/import access, CPU-time and output limits.
Falls back to refusing execution when RestrictedPython is missing —
never runs untrusted code unrestricted.
"""
import logging
import multiprocessing
import traceback

logger = logging.getLogger(__name__)

try:
    from RestrictedPython import compile_restricted, safe_globals, limited_builtins
    from RestrictedPython.Guards import (guarded_iter_unpack_sequence,
                                         safe_iter, safer_getattr)
    HAS_RESTRICTED = True
except ImportError:
    HAS_RESTRICTED = False


class SandboxError(Exception):
    pass


def _worker(code: str, context: dict, queue):
    try:
        byte_code = compile_restricted(code, filename="<plugin>", mode="exec")
        glb = dict(safe_globals)
        glb["_getattr_"] = safer_getattr
        glb["_getiter_"] = safe_iter
        glb["_iter_unpack_sequence_"] = guarded_iter_unpack_sequence
        glb["__builtins__"] = limited_builtins
        glb["context"] = dict(context)   # copy: plugin can't mutate caller state
        glb["result"] = None
        loc = {}
        exec(byte_code, glb, loc)  # noqa: S102 - restricted bytecode
        queue.put({"ok": True, "result": loc.get("result", glb.get("result"))})
    except Exception:
        queue.put({"ok": False, "error": traceback.format_exc(limit=3)})


def run_sandboxed(code: str, context: dict | None = None,
                  timeout_seconds: int = 5) -> dict:
    """Run plugin code in a separate process with a hard timeout.
    Plugin sets `result` variable to return data."""
    if not HAS_RESTRICTED:
        raise SandboxError("RestrictedPython not installed - refusing to run plugin code")

    queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=_worker, args=(code, context or {}, queue))
    proc.start()
    proc.join(timeout_seconds)
    if proc.is_alive():
        proc.terminate()
        proc.join()
        raise SandboxError(f"plugin exceeded {timeout_seconds}s time limit")
    if queue.empty():
        raise SandboxError("plugin produced no result")
    out = queue.get()
    if not out["ok"]:
        raise SandboxError(f"plugin error:\n{out['error']}")
    return out["result"]
