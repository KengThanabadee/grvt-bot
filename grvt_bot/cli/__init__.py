"""
CLI module containing command-line interface.
"""

def main():
    from grvt_bot.cli.main import main as cli_main
    return cli_main()

__all__ = ["main"]
