import threading
import gc

def bytes_to_human(n):
    """Converts bytes to a human readable string (KB, MB, GB)."""
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n

def force_gc():
    """Forces a full garbage collection to keep RAM usage low."""
    gc.collect()

class SafeThread(threading.Thread):
    """A wrapper around threading.Thread that captures exceptions."""
    def __init__(self, target, args=()):
        super().__init__(target=target, args=args, daemon=True)
        self.start()

