from curses import KEY_DOWN
from enum import Enum
import random
import subprocess, shlex
import sys
import time
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
    K_PRESS = 99  # technically not a keystate but used for pyautogui for a combined down/up keypress


class Macro:
    def __init__(
        self, name: str, type: MacroType, value: str | Callable, args: dict = {}
    ):
        self.name = name
        self.macro_type = type
        self.macro_value = value
        self.macro_args = args

    def __call__(self, *args, **kwargs):
        """When the object is called this will attempt to run the method with the same name as the macro type"""
        getattr(self, self.macro_type.name)(*args, **kwargs)

    def M_PRINT(self):
        """Type a block of text onto the keyboard"""
        pyautogui.write(self.macro_value)

    def M_TYPE(self):
        """Type a series of keypresses including control keys."""
        # TODO: In the future, improve this method such that the pyautogui calls are generated \
        #   when the macro is registered rather than parsing macro_value each time.
        delay = self.macro_args.get("delay", 0.01)
        delay_randomness = self.macro_args.get("delay_randomness", 0)

        for k in self.macro_value:
            (key, state) = k
            match state:
                case KeyState.K_PRESS:
                    pyautogui.press(key)
                case KeyState.K_DOWN:
                    pyautogui.keyDown(key)
                case KeyState.K_UP:
                    pyautogui.keyUp(key)
            time.sleep(
                delay + round(random.uniform(-delay_randomness, delay_randomness), 2)
            )

    def M_SHELL(self):
        """Run a shell command and type the output."""
        # TODO: change this so it can use the clipboard (xsel or xclip) instead of typing the output
        pyautogui.write(
            subprocess.check_output(shlex.split(self.macro_value), shell=True).decode(
                "utf-8"
            )
        )

    def M_EXEC(self):
        """Run a program"""
        subprocess.Popen(shlex.split(self.macro_value))

    def M_PYTHON(self):
        """Excute a Python method"""
        pass


class MacroDevice:
    def __init__(self, evdev_path: str, grab=True, debug=False):
        self.__macros = {}

        try:
            print(f"Opening device: {evdev_path}")
            self.__evdev = evdev.InputDevice(evdev_path)
            if grab:
                self.__evdev.grab()
        except Exception as e:
            sys.exit(f"Failed to open evdev device: {e}")

        self.debug = debug

    def register_macro(
        self,
        key: Any,
        state: KeyState,
        macro: Macro,
    ) -> bool:
        """Registers a Macro() object to a keypress and state. (e.g pressing down the enter key)"""
        if key not in self.__macros:
            self.__macros[key] = {}

        if state in self.__macros[key]:
            print("Failed to register macro: Key already assigned.")
            return False
        else:
            self.__macros[key][state.name] = macro
            print(
                f'Bound macro "{macro.name}" to key {evdev.ecodes.KEY[key]} {state.name}.'
            )
            return True

    def unregister_macro(self, key: evdev.ecodes, state: KeyState) -> bool:
        """Checks for and removes a specified macro."""
        if macro := self.__macros.get(key, {}).pop(state.name, None):
            print('Unbound macro "{macro.name}" from {key} on {state.name}.')
            return True
        else:
            print("Failed to remove macro: Key not bound.")
            return True

    def event_loop(self) -> None:
        """Main keyboard even loop

        This reads from evdev in a loop filtering for key events. If found,
        it then executes them based on whatever the macro is set to do.
        """
        for ev in self.__evdev.read_loop():
            if ev.type != evdev.ecodes.EV_KEY:
                continue

            if self.debug:
                print(evdev.categorize(ev))

            if macro := self.__macros.get(ev.code, {}).get(
                KeyState(ev.value).name, None
            ):
                macro()
