'''
Init
'''
# pylint: disable=wildcard-import
try:
    print("Trying import dev.py settings...")
    from .development import *
except ImportError:
    try:
        print("Trying import testing.py settings...")
        from .staging import *
    except ImportError:
        print("Trying import production.py settings...")
        from .production import *
