from contextlib import redirect_stdout
import importlib
import io
import shlex
import subprocess
import sys
import time
import re
from enum import Enum
from os.path import basename, dirname, realpath
from typing import Any, Callable

import evdev
import pyautogui

try:
    import pyperclip

    PYPERCLIP_AVAILABLE = True
except ImportError:
    print("WARN: Unable to load Pyperclip. Pasting the output of macros will fallback to typing.")
    print("To install Pyperclip please run the following command: pip3 install pyperclip")
    PYPERCLIP_AVAILABLE = False

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
    def __init__(self, name: str, mtype: MacroType, value: str | Callable, args: dict = None):
        self.name = name
        self.macro_type = mtype
        self.macro_value = value
        self.macro_args = args

    def __call__(self, *args, **kwargs):
        """When the object is called this will attempt to run the method with the same name as the macro type"""
        out = getattr(self, self.macro_type.name)(*args, **kwargs)
        if out is not None:
            if self.macro_args.get("newline", True):
                out += "\n"

            if self.macro_args.get("paste_output", False) and PYPERCLIP_AVAILABLE:
                previous = pyperclip.paste()
                pyperclip.copy(out)
                with pyautogui.hold("ctrl"):
                    pyautogui.press("v")
                pyperclip.copy(previous)
            else:
                pyautogui.write(out)

    def M_PRINT(self):
        """Type a block of text onto the keyboard"""
        return self.macro_value

    def M_TYPE(self):
        """Type a series of keypresses including control keys."""
        # TODO: In the future, improve this method such that the pyautogui calls are generated \
        #   when the macro is registered rather than parsing macro_value each time.
        delay = self.macro_args.get("delay", 0.01)

        keypresses = filter(lambda x: x != "", self.macro_value.split(" "))

        held_modifiers = {}

        for k in keypresses:
            # (key, state) = k

            for modifier, keys_remaining in list(held_modifiers.items()):
                if keys_remaining < 1:
                    pyautogui.keyUp(modifier)
                    held_modifiers.pop(modifier)
                    continue
                held_modifiers[modifier] -= 1

            # press and hold key. e.g +shift holds the shift key down
            if len(k) > 1 and k[0] == "+":
                pyautogui.keyDown(k[1:])
            # release held key. e.g -shift releases the shift key
            elif len(k) > 1 and k[0] == "-":
                pyautogui.keyUp(k[1:])
            # TODO: This could be written better but it does the job for now.
            elif len(k) > 1 and k[0] == "=":
                hold_times = re.search(r"\d+", k)
                if hold_times is None:
                    hold_times = 1
                    modifier = k[1:]
                else:
                    hold_times = int(hold_times.group())
                    modifier = k.replace(f"={hold_times}", "")

                if modifier != "":
                    held_modifiers[modifier.lower()] = hold_times
                    pyautogui.keyDown(modifier)
            else:  # press and release the key
                pyautogui.press(k)
            # match state:
            #     case KeyState.K_PRESS:
            #         pyautogui.press(key)
            #     case KeyState.K_DOWN:
            #         pyautogui.keyDown(key[1:])
            #     case KeyState.K_UP:
            #         pyautogui.keyUp(key)

            time.sleep(delay)

        return

    def M_SHELL(self):
        """Run a shell command and type the output."""
        callable_out = io.StringIO()
        with redirect_stdout(callable_out):
            sys.stdout.write(subprocess.check_output(self.macro_value, shell=True).decode("utf-8"))
        return callable_out.getvalue()

    def M_EXEC(self):
        """Run a program"""
        proc = subprocess.Popen(shlex.split(self.macro_value), stdout=subprocess.PIPE)

        # Read the program's stdout and type/paste it if background = False
        # Note: This blocks macro exection until the child exits and should only be used for short-running programs.
        if not self.macro_args.get("background", False):
            return proc.stdout.read().decode()

    def M_PYTHON(self):
        """Excute a Python method"""
        script_path = dirname(realpath(self.macro_value["path"]))
        script_filename = basename(realpath(self.macro_value["path"])).split(".")[0]
        if script_path not in sys.path:
            sys.path.append(script_path)

        try:
            # Try to import the user's specified script file as a module
            lib = importlib.import_module(script_filename)
            callable_out = io.StringIO()
            with redirect_stdout(callable_out):
                # Get the method and execute it, capturing stdout
                getattr(lib, self.macro_value["method"])()
            return callable_out.getvalue()
        except (ModuleNotFoundError, AttributeError):
            print(
                f"Failed to run macro '{self.name}'. Check that the method '{self.macro_value['method']} exists in the script '{self.macro_value['path']} and reload the config."
            )
            return


class MacroDevice:
    def __init__(self, evdev_path: str, grab=True, debug=False):
        self.__macros = {}
        self.grab = grab

        try:
            print(f"Opening device: {evdev_path}")
            self.__evdev = evdev.InputDevice(evdev_path)
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
            print(f'Unbound macro "{macro.name}" from {key} on {state.name}.')
            return True
        else:
            print("Failed to remove macro: Key not bound.")
            return False

    def run(self) -> None:
        if self.grab:
            self.__evdev.grab()

        self.event_loop()

        if self.grab:
            self.__evdev.ungrab()

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
