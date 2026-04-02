"""Bridge Master — GUI application entry point.

Launch the Bridge Master training tool with a graphical interface.

Usage:
    python bridge.py
"""

from bridge.gui import BridgeMasterApp


def main():
    app = BridgeMasterApp()
    app.setup()
    app.run()


if __name__ == "__main__":
    main()
