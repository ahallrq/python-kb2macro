import importlib
import io
import shlex
import subprocess
import sys
import time
from contextlib import redirect_stdout
from enum import Enum
from os.path import basename, dirname, realpath
from typing import Any, Callable

import evdev
import pyautogui
import pyperclip

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
    def __init__(self, name: str, mtype: MacroType, value: str | Callable, args: dict = {}):
        self.name = name
        self.macro_type = mtype
        self.macro_value = value
        self.macro_args = args

    def paste_output(self, p: Any):
        out = ""
        if callable(p):
            callable_out = io.StringIO()
            with redirect_stdout(callable_out):
                p()
            out = callable_out.getvalue()
        else:
            out = str(p)
        pyperclip.copy(out)
        with pyautogui.hold("ctrl"):
            pyautogui.press("v")

    def __call__(self, *args, **kwargs):
        """When the object is called this will attempt to run the method with the same name as the macro type"""
        getattr(self, self.macro_type.name)(*args, **kwargs)

    def M_PRINT(self):
        """Type a block of text onto the keyboard"""
        paste_output = self.macro_args.get("paste_output", False)
        self.paste_output(self.macro_value) if paste_output else pyautogui.write(self.macro_value)

    def M_TYPE(self):
        """Type a series of keypresses including control keys."""
        # TODO: In the future, improve this method such that the pyautogui calls are generated \
        #   when the macro is registered rather than parsing macro_value each time.
        delay = self.macro_args.get("delay", 0.01)

        for k in self.macro_value:
            (key, state) = k
            match state:
                case KeyState.K_PRESS:
                    pyautogui.press(key)
                case KeyState.K_DOWN:
                    pyautogui.keyDown(key)
                case KeyState.K_UP:
                    pyautogui.keyUp(key)
            time.sleep(delay)

    def M_SHELL(self):
        """Run a shell command and type the output."""
        paste_output = self.macro_args.get("paste_output", True)

        output = subprocess.check_output(self.macro_value, shell=True).decode("utf-8")

        if paste_output:
            self.paste_output(output)
        else:
            pyautogui.write(output)

    def M_EXEC(self):
        """Run a program"""
        subprocess.Popen(shlex.split(self.macro_value))

    def M_PYTHON(self):
        """Excute a Python method"""
        paste_output = self.macro_args.get("paste_output", False)

        script_path = dirname(realpath(self.macro_value["path"]))
        script_filename = basename(realpath(self.macro_value["path"])).split(".")[0]
        if script_path not in sys.path:
            sys.path.append(script_path)

        lib = importlib.import_module(script_filename)
        method = getattr(lib, self.macro_value["method"])

        self.paste_output(method) if paste_output else method()


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

        if state.name in self.__macros[key]:
            print("Failed to register macro: Key already assigned.")
            return False
        else:
            self.__macros[key][state.name] = macro
            print(f'Bound macro "{macro.name}" to key {evdev.ecodes.KEY[key]} {state.name}.')
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
        """Main keyboard event loop

        This reads from evdev in a loop filtering for key events. If found,
        it then executes them based on whatever the macro is set to do.
        """
        for ev in self.__evdev.read_loop():
            if ev.type != evdev.ecodes.EV_KEY:
                continue

            if self.debug:
                print(evdev.categorize(ev))

            if macro := self.__macros.get(ev.code, {}).get(KeyState(ev.value).name, None):
                macro()
