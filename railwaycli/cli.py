#!/usr/bin/env python3
"""CLI tool for Israel Railways."""

import fire
import israelrailapi
from datetime import datetime
import pytz
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import re
import sys

from .railway import RailwayCLI


def main():
    """Entry point for the CLI tool."""
    try:
        fire.Fire(RailwayCLI)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
