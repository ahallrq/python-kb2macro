from enum import Enum
import subprocess, shlex
import sys
from typing import Any, Callable
import evdev
import pyautogui

pyautogui.PAUSE = 0


class MacroType(Enum):
    M_PRINT = 1  # Type out a block of text
    M_TYPE = 2  # Press a series of keys or mouse buttons
    M_EXEC = 3  # Run a program
    M_SHELL = 4  # Run a shell command
    M_PYTHON = 5  # Run a Python function


class KeyState(Enum):
    K_UP = 0
    K_DOWN = 1
    K_HOLD = 2


class Macro:
    def __init__(self, name: str, type: MacroType, value: str | Callable):
        self.name = name
        self.macro_type = type
        self.macro_value = value

    def __call__(self):
        getattr(self, self.macro_type.name)()

    def M_PRINT(self):
        pyautogui.write(self.macro_value)

    def M_TYPE(self):
        pass

    def M_SHELL(self):
        pyautogui.write(
            subprocess.check_output(shlex.split(self.macro_value), shell=True).decode(
                "utf-8"
            )
        )

    def M_EXEC(self):
        subprocess.Popen(shlex.split(self.macro_value))

    def M_PYTHON(self):
        pass


class MacroDevice:
    def __init__(self, evdev_path: str, grab=True):
        self.__macros = {}

        try:
            print(f"Opening device: {evdev_path}")
            self.__evdev = evdev.InputDevice(evdev_path)
            if grab:
                self.__evdev.grab()
        except Exception as e:
            sys.exit(f"Failed to open evdev device: {e}")

    def register_macro(
        self,
        key: Any,
        state: KeyState,
        macro: Macro,
    ) -> bool:
        if key not in self.__macros:
            self.__macros[key] = {}

        if state in self.__macros[key]:
            print("Failed to register macro: Key already assigned.")
            return False
        else:
            self.__macros[key][state] = macro
            print(
                f'Bound macro "{macro.name} to key {evdev.ecodes.KEY[key]} {state.name}.'
            )
            return True

    def unregister_macro(self, key: evdev.ecodes, state: KeyState) -> bool:
        if key in self.__macros and state in self.__macros[key]:
            self.__macros[key].pop(state)
            return True
        else:
            print("Failed to remove macro: Key not bound.")
            return True

    def run_macro(self, key: evdev.ecodes, state: KeyState) -> None:
        pass

    def event_loop(self) -> None:
        for ev in self.__evdev.read_loop():
            if ev.type != evdev.ecodes.EV_KEY:
                continue

            if macro := self.__macros.get(ev.code, {}).get(ev.value, None):
                macro()
