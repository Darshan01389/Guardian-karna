# Guardian Karna
Guardian Karna is a desktop browser prototype focused on safe browsing, background security scans, performance monitoring, and simple community features. It uses **PyQt6** for the UI and includes a small mini‑game.

## Prerequisites & Dependencies

This project requires the following Python packages:

```
PyQt6
PyQt6-WebEngine
psutil
```

You can install them with pip:

```bash
pip install -r requirements.txt
```

> **Note:** the workspace does not include the `icon/warrior.png` file used by the UI. If the icon folder is missing you will see a warning on startup, but the application will still run.

## Running

```bash
python main.py
```

If PyQt6 is not installed the program will exit with an error message instructing you to install the required packages.

## Packaging & Deployment

The application is a PyQt6‑based desktop program. You can treat the repository as a
normal Python project using the included `pyproject.toml` / `setup.cfg`. After
cloning:

```bash
python -m pip install --upgrade pip build
python -m pip install -e .      # installs guardian-karna as a package
```

This also creates a `guardian-karna` console script so you can run `guardian-karna`
directly instead of `python main.py`.

For making a distributable bundle, tools like [PyInstaller](https://www.pyinstaller.org/)
work well. A minimal `main.spec` file is included in the repo. To build, install
PyInstaller and run:

```bash
pip install pyinstaller
pyinstaller main.spec
```

*Note:* the build environment must provide a Python shared library (the default
Ubuntu packages do). In some container/CI images Python is built without a shared
library, which prevents a build and will print an error during analysis. In that
case run the packaging step on a normal machine or inside a virtualenv created by
the system Python.

The produced `dist/main` directory will contain a self‑contained application bundle.
Copy the `icon/warrior.png` (or an `.ico`/`.icns` variant) into the bundle if you
want the graphical icon to appear.

For cross‑platform distribution you may need to run the packaging step on each
target OS.

Finally, any deployment should begin by installing the packages listed in
`requirements.txt` and running the unit tests (`pytest`) to ensure the code is up
to date and passes the internal checks (see below).

*Note:* the build environment must provide a Python shared library (the default
Ubuntu packages do). In some container/CI images Python is built without a shared
library, which prevents a build and will print an error during analysis. In that
case run the packaging step on a normal machine or inside a virtualenv created by
the system Python.

The produced `dist/main` directory will contain a self‑contained application bundle.
Copy the `icon/warrior.png` (or an `.ico`/`.icns` variant) into the bundle if you
want the graphical icon to appear.

For cross‑platform distribution you may need to run the packaging step on each
target OS.

Finally, any deployment should begin by installing the packages listed in
`requirements.txt` and running the unit tests (`pytest`) to ensure the code is up
to date and passes the internal checks (see below).

## Project Structure

- `main.py` – entry point\
- `browser_window.py` – main UI logic and browser features\
- `mode_manager.py` – security mode/subscription logic\
- `security_engine.py` – simulated risk classifier and scan routines\
- `performance_monitor.py` – CPU/memory/network tracking using psutil\
- `games.py` – simple click‑counting mini‑game and stats dialogs\
- `auth.py` – user account simulation and login dialog\
- `log_manager.py` – stores scan events\
- `styles.py` – Qt stylesheet strings for dark/light themes

Please refer to the source files for implementation details.
