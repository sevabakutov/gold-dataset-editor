"""CLI entry point for gold dataset editor."""

import click
from pathlib import Path


@click.command()
@click.option(
    "--data-root",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Root directory containing JSONL files",
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind to",
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Port to bind to",
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
def main(data_root: Path, host: str, port: int, reload: bool) -> None:
    """Start the Gold Dataset Editor web application."""
    import uvicorn
    from gold_dataset_editor.config import settings

    # Update settings with CLI options
    settings.data_root = data_root.resolve()

    click.echo(f"Starting Gold Dataset Editor...")
    click.echo(f"Data root: {settings.data_root}")
    click.echo(f"Open http://{host}:{port} in your browser")

    uvicorn.run(
        "gold_dataset_editor.app:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
