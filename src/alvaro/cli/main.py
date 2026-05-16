from __future__ import annotations

import typer
from loguru import logger

from alvaro.cli.analytics import app as analytics_app
from alvaro.cli.generate import app as generate_app
from alvaro.cli.upload import app as upload_app

app = typer.Typer(name="alvaro", help="YT Shorts automation pipeline", no_args_is_help=True)
app.add_typer(generate_app, name="generate")
app.add_typer(upload_app, name="upload")
app.add_typer(analytics_app, name="analytics")


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
