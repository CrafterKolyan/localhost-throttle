import sys

from .run_with_ctrl_handler import run_with_ctrl_handler


def main():
  run_with_ctrl_handler(*sys.argv[1:])
