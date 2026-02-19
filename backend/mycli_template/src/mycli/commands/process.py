import click

@click.command(name="process")
@click.option("--input", required=True, help="Input file path")
@click.option("--verbose", is_flag=True, help="Enable verbose logging")
def process_cmd(input, verbose):
    """Process input file."""
    if verbose:
        click.echo(f"[DEBUG] Processing file: {input}")
    click.echo(f"Processing {input} complete.")