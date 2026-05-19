from __future__ import annotations

import typer
from loguru import logger

from alvaro.cli.analytics import analytics_cmd
from alvaro.cli.generate import generate_cmd
from alvaro.cli.upload import upload_cmd

app = typer.Typer(name="alvaro", help="YT Shorts automation pipeline", no_args_is_help=True)
app.command(name="generate")(generate_cmd)
app.command(name="upload")(upload_cmd)
app.command(name="analytics")(analytics_cmd)


@app.callback()
def _setup(verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    if not verbose:
        logger.remove()
        logger.add(lambda msg: typer.echo(msg, err=True), level="INFO", colorize=True)


@app.command()
def version() -> None:
    from alvaro import __version__

    typer.echo(f"alvaro {__version__}")


if __name__ == "__main__":
    app()
