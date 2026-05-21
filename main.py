# main.py
from services.args_parser import cli
from services.debug_logger import Debug

if __name__ == "__main__":
    cli.run() # typer args_parser
