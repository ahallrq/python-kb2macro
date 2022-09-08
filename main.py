import sys
import evdev
from evdev import ecodes
import pyautogui
import macro


EVDEV_DEVICE = "/dev/input/macro0"


def main():
    m = macro.MacroDevice(EVDEV_DEVICE)
    m.register_macro(
        ecodes.KEY_KP0,
        macro.KeyState.K_DOWN,
        macro.Macro(
            "type some text",
            macro.MacroType.M_PRINT,
            "He just kept talking in one long incredibly unbroken sentence moving from topic to topic so that no-one had a chance to interrupt; it was really quite hypnotic.\n",
        ),
    )
    m.register_macro(
        ecodes.KEY_KP0,
        macro.KeyState.K_DOWN,
        macro.Macro(
            "paste some text",
            macro.MacroType.M_PRINT,
            "He just kept talking in one long incredibly unbroken sentence moving from topic to topic so that no-one had a chance to interrupt; it was really quite hypnotic.\n",
            {"paste_output": True},
        ),
    )
    m.register_macro(
        ecodes.KEY_KPENTER,
        macro.KeyState.K_DOWN,
        macro.Macro("type the date", macro.MacroType.M_SHELL, "date"),
    )
    m.register_macro(
        ecodes.KEY_KP3,
        macro.KeyState.K_DOWN,
        macro.Macro(
            "paste the date", macro.MacroType.M_SHELL, "date", {"paste_output": True}
        ),
    )
    m.register_macro(
        ecodes.KEY_KPPLUS,
        macro.KeyState.K_DOWN,
        macro.Macro("run a program", macro.MacroType.M_EXEC, "/usr/bin/kwrite"),
    )
    m.register_macro(
        ecodes.KEY_KPMINUS,
        macro.KeyState.K_DOWN,
        macro.Macro(
            "press a series of keys",
            macro.MacroType.M_TYPE,
            [
                ("shift", macro.KeyState.K_DOWN),
                ("H", macro.KeyState.K_PRESS),
                ("shift", macro.KeyState.K_UP),
                ("e", macro.KeyState.K_PRESS),
                ("l", macro.KeyState.K_PRESS),
                ("l", macro.KeyState.K_PRESS),
                ("o", macro.KeyState.K_PRESS),
                ("space", macro.KeyState.K_PRESS),
                ("shift", macro.KeyState.K_DOWN),
                ("w", macro.KeyState.K_PRESS),
                ("shift", macro.KeyState.K_UP),
                ("o", macro.KeyState.K_PRESS),
                ("r", macro.KeyState.K_PRESS),
                ("l", macro.KeyState.K_PRESS),
                ("d", macro.KeyState.K_PRESS),
                ("!", macro.KeyState.K_PRESS),
            ],
            {"delay": 0.100},
        ),
    )
    m.register_macro(
        ecodes.KEY_KP9,
        macro.KeyState.K_DOWN,
        macro.Macro(
            "run a python method",
            macro.MacroType.M_PYTHON,
            {
                "path": "/home/andrew/Temp/macrotestscript.py",
                "method": "testfunc",
                "args": [],
                "kwargs": {},
            },
            {"paste_output": True},
        ),
    )

    m.event_loop()
    m.__evdev.ungrab()


if __name__ == "__main__":
    main()
