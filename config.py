import json
import sys

from evdev import ecodes
from python_json_config import ConfigBuilder

import macro

default_config = json.loads('{ "device" : "/dev/input/macro0", "enable_paste" : true, "macros" : [] }')


def is_valid_macro_config(m):
    # TODO: if x.get(thing) not in y or if (res := y.get(x.get())) is not None

    for m_item in m:
        if not isinstance(m_item.get("name", None), str):
            return False, "Macro argument 'name' is missing or is the wrong type."

        if m_item.get("key", None) not in ecodes.ecodes:
            return False, "Macro argument 'key' is missing or is the wrong type."

        if m_item.get("state", None) not in macro.KeyState.__members__:
            return False, "Macro argument 'state' is missing or is the wrong type."

        if m_item.get("type", None) not in macro.MacroType.__members__:
            return False, "Macro argument 'type' is missing or is the wrong type."

        # TODO: Extra validation for macro type macro.M_TYPE

        if not isinstance(m_item.get("value", None), str):
            return False, "Macro argument 'value' is missing or is the wrong type."

        if not isinstance(m_item.get("args", None), dict):
            return False, "Macro argument 'args' is missing or is the wrong type."

    return True


# TODO: Improve error messages for config errors

builder = ConfigBuilder()
builder.set_field_access_required()
builder.add_optional_fields(["enable_paste"])
builder.validate_field_type("device", str)
builder.validate_field_type("enable_paste", bool)
builder.validate_field_type("macros", list)
builder.validate_field_value("macros", is_valid_macro_config)


def load_config(f):
    try:
        config = builder.parse_config(f)
    except AssertionError as e:
        sys.exit(f"An error occurred while loading the config file: {f}\n{str(e)}")

    macro_tmp = macro.MacroDevice(config.device)
    for m in config.macros:
        macro_tmp.register_macro(
            ecodes.ecodes[m["key"]],
            macro.KeyState[m["state"]],
            macro.Macro(
                m["name"],
                macro.MacroType[m["type"]],
                m["value"],
                m["args"],
            ),
        )

    return macro_tmp
