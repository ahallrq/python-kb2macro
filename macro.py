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
        state: int,
        type: MacroType,
        value: str | Callable,
    ) -> bool:
        if key not in self.__macros:
            self.__macros[key] = {}

        if state in self.__macros[key]:
            print("Failed to register macro: Key already assigned.")
            return False
        else:
            self.__macros[key][state] = {"type": type, "value": value}
            print(
                f'Bound macro {type} "{value}" to key {evdev.ecodes.KEY[key]} {state}.'
            )
            return True

    def unregister_macro(self, key: evdev.ecodes, state: int) -> bool:
        if key in self.__macros and state in self.__macros[key]:
            self.__macros[key].pop(state)
            return True
        else:
            print("Failed to remove macro: Key not bound.")
            return True

    def run_macro(self, key: evdev.ecodes, state: int) -> None:
        pass

    def event_loop(self) -> None:
        for ev in self.__evdev.read_loop():
            if ev.type != evdev.ecodes.EV_KEY:
                continue

            if macro := self.__macros.get(ev.code, {}).get(ev.value, None):
                match macro["type"]:
                    case MacroType.M_PRINT:
                        pyautogui.write(macro["value"])
                    case MacroType.M_TYPE:
                        pass
                    case MacroType.M_SHELL:
                        pyautogui.write(
                            subprocess.check_output(
                                shlex.split(macro["value"]), shell=True
                            ).decode("utf-8")
                        )
                    case MacroType.M_EXEC:
                        subprocess.Popen(shlex.split(macro["value"]))
                    case MacroType.M_PYTHON:
                        pass
                    case _:
                        continue
