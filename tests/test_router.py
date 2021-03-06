import sys
import inspect
from pathlib import Path

__here = Path(__file__).resolve().parent
sys.path.append(str(__here.parent))

from unittest.mock import Mock

from line_bot_router import Router, reply_only


ADMIN_ID = "ADMIN_ID"


Event = Mock


def _make_evt(msg: str) -> Event:
    event = Event()
    event.message.text = msg
    event.source.user_id = "non_admin"
    return event


def _admin_evt(msg: str) -> Event:
    event = _make_evt(msg)
    event.source.user_id = ADMIN_ID
    return event


root = Router(default="ROOT MISMATCH")


# helper function
def get_function_name() -> str:
    """Return caller's function name"""
    return inspect.stack()[1][3]


@root.register("^cmd1$", default="cmd1 mismatch")
def cmd1(event):
    """cmd1: base description"""
    return get_function_name()


@cmd1.register(r"^arg[1-3]$", default="cmd1 arg1 mismatch")
def cmd1_arg1(event):
    """cmd1 arg1-3: description"""
    return get_function_name()


@cmd1_arg1.register("^opt[12]$")
def cmd1_arg1_opt1(event):
    return get_function_name()


@reply_only(ADMIN_ID, default="ADMIN ONLY")
@cmd1.register(r"^arg[67]$")
def cmd1_arg2(event):
    """cmd1 arg[67]: admin only"""
    return get_function_name()


@cmd1_arg2.register("^opt[ABC]$")
def cmd1_arg2_opt(event):
    """cmd1 arg[67] opt[ABC]: description"""
    return get_function_name()


@cmd1_arg2.register("^opt[DEF]$")
def cmd1_arg2_opt2(event):
    return get_function_name()


@root.register("^cmd2$")
def cmd2(event):
    """cmd2: desc"""
    return get_function_name()


@reply_only(ADMIN_ID)
@root.register("^cmd3$")
def cmd3_admin(event):
    return get_function_name()


@root.register("^cmd3$")
def cmd3_normal(event):
    return get_function_name()


def test_root_description():
    desc_text = (
        """cmd1: base description\n"""
        + """cmd1 arg1-3: description\n"""
        + """cmd1 arg[67]: admin only\n"""
        + """cmd1 arg[67] opt[ABC]: description\n"""
        + """cmd2: desc"""
    )
    assert desc_text == root.make_description_text()


def test_cmd1_description():
    desc_text = (
        """cmd1: base description\n"""
        + """cmd1 arg1-3: description\n"""
        + """cmd1 arg[67]: admin only\n"""
        + """cmd1 arg[67] opt[ABC]: description"""
    )
    assert desc_text == cmd1.make_description_text()


def test_cmd1_arg2_description():
    desc_text = (
        """cmd1 arg[67]: admin only\n""" + """cmd1 arg[67] opt[ABC]: description"""
    )
    print(cmd1_arg2.make_description_text())
    assert desc_text == cmd1_arg2.make_description_text()


def test_cmd1_match():
    msg = "cmd1"
    assert root.process(_make_evt(msg)) == "cmd1"


def test_cmd1_mismatch():
    msg = "cmd11"
    assert root.process(_make_evt(msg)) == "ROOT MISMATCH"


def test_cmd2_match():
    msg = "cmd2"
    assert root.process(_make_evt(msg)) == "cmd2"


def test_cmd2_mismatch():
    msg = "cmd2a"
    assert root.process(_make_evt(msg)) == "ROOT MISMATCH"


def test_cmd1_arg1_match():
    msg = "cmd1 arg1"
    assert root.process(_make_evt(msg)) == "cmd1_arg1"

    msg = "cmd1 arg2"
    assert root.process(_make_evt(msg)) == "cmd1_arg1"

    msg = "cmd1 arg3"
    assert root.process(_make_evt(msg)) == "cmd1_arg1"


def test_cmd1_arg1_mismatch():
    msg = "cmd1 arg4"
    assert root.process(_make_evt(msg)) == "cmd1 mismatch"


def test_cmd1_arg1_opt_match():
    msg = "cmd1 arg2 opt1"
    assert root.process(_make_evt(msg)) == "cmd1_arg1_opt1"


def test_cmd1_arg2_user_match():
    msg = "cmd1 arg6"
    event = _admin_evt(msg)
    assert root.process(event) == "cmd1_arg2"


def test_cmd1_arg2_user_mismatch():
    msg = "cmd1 arg6"
    event = _make_evt(msg)
    assert root.process(event) == "ADMIN ONLY"


def test_cmd1_arg2_opt_user_match():
    msg = "cmd1 arg6 optA"
    event = _admin_evt(msg)
    assert root.process(event) == "cmd1_arg2_opt"


def test_cmd1_arg2_opt_user_mismatch():
    msg = "cmd1 arg6 optA"
    event = _make_evt(msg)
    assert root.process(event) == "ADMIN ONLY"


def test_cmd1_arg2_opt2_user_match():
    msg = "cmd1 arg6 optE"
    event = _admin_evt(msg)
    assert root.process(event) == "cmd1_arg2_opt2"


def test_cmd1_arg2_opt2_user_mismatch():
    msg = "cmd1 arg6 optE"
    event = _make_evt(msg)
    assert root.process(event) == "ADMIN ONLY"


def test_cmd3_admin():
    msg = "cmd3"
    event = _admin_evt(msg)
    assert root.process(event) == "cmd3_admin"


def test_cmd3_normal():
    msg = "cmd3"
    event = _make_evt(msg)
    assert root.process(event) == "cmd3_normal"
