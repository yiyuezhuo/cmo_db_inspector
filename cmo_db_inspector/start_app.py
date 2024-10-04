
import argparse
from pathlib import Path
from . import App

parser = argparse.ArgumentParser()
parser.add_argument("cmo_db_root", help=r"Location to store CMO database files, example: D:\SteamLibrary\steamapps\common\Command - Modern Operations\DB")
args = parser.parse_args()

cmo_db_root = Path(args.cmo_db_root)
app = App(cmo_db_root).create()
app.demo.launch()
