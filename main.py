import sys
import evdev
from evdev import ecodes
import pyautogui
import macro

# udev rule: SUBSYSTEM=="input", ATTRS{id/vendor}=="xxxx", ATTRS{id/product}=="yyyy", MODE="0660", GROUP="somegroup", SYMLINK+="input/macroN"

EVDEV_DEVICE = "/dev/input/macro0"


def main():
    m = macro.MacroDevice(EVDEV_DEVICE, grab=True)
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

    m.event_loop()
    m.__evdev.ungrab()


if __name__ == "__main__":
    main()
