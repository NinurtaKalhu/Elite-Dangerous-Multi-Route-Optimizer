import sys
import logging
import traceback

def main():
    def global_exception_hook(exctype, value, tb):
        logging.basicConfig(level=logging.INFO)
        logging.error("\n--- Uncaught Exception ---\n" + ''.join(traceback.format_exception(exctype, value, tb)))
        sys.__excepthook__(exctype, value, tb)
    sys.excepthook = global_exception_hook
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import main
if __name__ == "__main__":
    main()
