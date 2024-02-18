import signal
import sys
import logging

class SignalHandler:
    @staticmethod
    def signal_handler(sig, frame):
        logging.info("Ctrl+C detected. Exiting gracefully...")
        sys.exit(0)
