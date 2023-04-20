import json
from pathlib import Path
import sys
import macro
from evdev import ecodes
from python_json_config import ConfigBuilder


default_config = json.loads('{ "device" : "/dev/input/macro0", "enable_paste" : true, "macros" : [] }')


def is_valid_macro_config(m):
    for m_item in m:
        if not isinstance(m_item.get("name", None), str):
            return False, "Macro argument 'name' is missing or is the wrong type."

        try:
            ecodes.ecodes[m_item.get("key", None)]
        except:
            return False, "Macro argument 'key' is missing or is the wrong type."

        try:
            macro.KeyState[m_item.get("state", None)]
        except:
            return False, "Macro argument 'state' is missing or is the wrong type."

        try:
            macro.MacroType[m_item.get("type", None)]
        except:
            return False, "Macro argument 'type' is missing or is the wrong type."

        # TODO: Extra validation for macro type macro.M_TYPE

        # FIXME:HACK: test

        if not isinstance(m_item.get("value", None), str):
            return False, "Macro argument 'value' is missing or is the wrong type."

        if not isinstance(m_item.get("args", None), dict):
            return False, "Macro argument 'args' is missing or is the wrong type."

    return True


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
    except Exception as e:
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
