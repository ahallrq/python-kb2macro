# python-kb2macro

python-kb2macro is a script written in Python that uses extra USB input devices to run macros.

At the moment, this only works on Linux due to its dependancy on evdev.

The script is a WIP and a bit of a mess at the moment.

### Udev Rules

Use of this program requires direct access to the event device of your chosen keyboard/numpad, typically only allowed by superusers. It is not recommended to run this as root but instead install the [example udev rules file](99-usb-macro-keyboard.rules) included.

Follow these steps to do so:

1. Modify the [99-usb-macro-keyboard.rules](99-usb-macro-keyboard.rules) file according to the instructions contained in the file.
2. Install the file to the `/etc/udev/rules.d/` directory.
3. Reload and the udev rules with elevated privileges: `# udevadm control --reload; udevadm trigger`