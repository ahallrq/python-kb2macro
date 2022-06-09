import sys
import evdev
from evdev import ecodes
import pyautogui
import macro

# udev rule: SUBSYSTEM=="input", ATTRS{id/vendor}=="xxxx", ATTRS{id/product}=="yyyy", MODE="0660", GROUP="somegroup", SYMLINK+="input/macroN"

EVDEV_DEVICE = "/dev/input/macro1"
DEBUG_KEYS = False


def main():
    m = macro.MacroDevice(EVDEV_DEVICE, grab=True, debug=DEBUG_KEYS)
    m.register_macro(
        ecodes.KEY_KP0,
        macro.KeyState.K_DOWN,
        macro.Macro("type some text", macro.MacroType.M_PRINT, "test\n"),
    )
    m.register_macro(
        ecodes.KEY_KPENTER,
        macro.KeyState.K_DOWN,
        macro.Macro("type the date", macro.MacroType.M_SHELL, "date"),
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

    m.event_loop()
    m.__evdev.ungrab()


if __name__ == "__main__":
    main()
