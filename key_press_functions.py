
# Here is a cross-platform solution, both blocking and non-blocking, not requiring any external libraries:
# from: https://stackoverflow.com/questions/24072790/how-to-detect-key-presses

import time
import contextlib as _contextlib

try:
    import msvcrt as _msvcrt

    # Length 0 sequences, length 1 sequences...
    _ESCAPE_SEQUENCES = [frozenset(("\x00", "\xe0"))]
 
    _next_input = _msvcrt.getwch

    _set_terminal_raw = _contextlib.nullcontext

    _input_ready = _msvcrt.kbhit

except ImportError:  # Unix
    import sys as _sys, tty as _tty, termios as _termios, \
        select as _select, functools as _functools

    # Length 0 sequences, length 1 sequences...
    _ESCAPE_SEQUENCES = [
        frozenset(("\x1b",)),
        frozenset(("\x1b\x5b", "\x1b\x4f"))]

    @_contextlib.contextmanager
    def _set_terminal_raw():
        fd = _sys.stdin.fileno()
        old_settings = _termios.tcgetattr(fd)
        try:
            _tty.setraw(_sys.stdin.fileno())
            yield
        finally:
            _termios.tcsetattr(fd, _termios.TCSADRAIN, old_settings)

    _next_input = _functools.partial(_sys.stdin.read, 1)

    def _input_ready():
        return _select.select([_sys.stdin], [], [], 0) == ([_sys.stdin], [], [])

_MAX_ESCAPE_SEQUENCE_LENGTH = len(_ESCAPE_SEQUENCES)

def _get_keystroke():
    key = _next_input()
    while (len(key) <= _MAX_ESCAPE_SEQUENCE_LENGTH and
           key in _ESCAPE_SEQUENCES[len(key)-1]):
        key += _next_input()
    return key

def _flush():
    while _input_ready():
        _next_input()

def key_pressed(key: str = None, *, flush: bool = True) -> bool:
    """Non Blocking, Return True if the specified key has been pressed

    Args:
        key: The key to check for. If None, any key will do.
        flush: If True (default), flush the input buffer after the key was found.
    
    Return:
        boolean stating whether a key was pressed.
    """
    with _set_terminal_raw():
        if key is None:
            if not _input_ready():
                return False
            if flush:
                _flush()
            return True

        while _input_ready():
            keystroke = _get_keystroke()
            if keystroke == key:
                if flush:
                    _flush()
                return True
        return False

def get_key(do_print=False) -> str:
    """Blocking, gets a key Print the key that was pressed

    Args:
        do_print (bool, optional): True prints key value. Defaults to False.

    Returns:
        str: key value in string format \\x##
    """
    with _set_terminal_raw():
        _flush()
        key_str=str("\\x" + "\\x".join(map("{:02x}".format, map(ord, _get_keystroke()))))
        if do_print:
            print(key_str)
        return key_str

def wait_key(key=None, *, pre_flush=False, post_flush=True) -> str:
    """Blocking, Wait for a specific key to be pressed.

    Args:
        key: The key to check for. If None, any key will do.
        pre_flush: If True, flush the input buffer before waiting for input.
        Useful in case you wish to ignore previously pressed keys.
        post_flush: If True (default), flush the input buffer after the key was
        found. Useful for ignoring multiple key-presses.
    
    Returns:
        The key that was pressed.
    """
    with _set_terminal_raw():
        if pre_flush:
            _flush()

        if key is None:
            key = _get_keystroke()
            if post_flush:
                _flush()
            return key

        while _get_keystroke() != key:
            pass
        
        if post_flush:
            _flush()

        return key
    
def wait_key_press_timeout(a_key=None,timeout=0):
    """Wait for a key press or timeout

    Args:
        a_key (_type_, optional): key in \\x## format. Defaults to None.
        timeout (int, optional): Time in seconds, 0 for infinite. Defaults to 0.

    Returns:
        bool: True, if key pressed, False if Timeout
    """
    start_time = time.time()
    while True:
        if key_pressed(a_key):
            return True #'Key Pressed!'
        if timeout>=0 and time.time() - start_time >= timeout: # timeout expired
            return False #"Time's up!"


if __name__ == "__main__":
    # You can use key_pressed() inside a while loop:
    print("Test 1")
    while True:
        time.sleep(1)
        print(time.time())
        if key_pressed():
            print("Key pressed exit test 1")
            break
    # You can also check for a specific key:

    print("Test 2 press arrow up")
    while True:
        time.sleep(1)
        print(time.time())
        if key_pressed("\x00\x48"):  # Up arrow key on Windows.
            print("Key pressed exit test 2")
            break
    # Find out special keys using get_key():  

    print("Press key to print: ctrl+c to exit -> \\x03")
    akey=''
    while akey!='\\x03':
        akey=get_key(True)
        time.sleep(0.33)
    # Press up key
    # \x00\x48
    # Or wait until a certain key is pressed:
    print("Test 3 waiting for 'a'")
    wait_key("a") # Stop and ignore all inputs until "a" is pressed.
    print("Finish waiting")

    print("10 seconds to press arrow up!") 
    print(wait_key_press_timeout('\x00\x48',10))