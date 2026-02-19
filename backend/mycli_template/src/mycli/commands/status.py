import click

@click.command(name="status")
def status_cmd():
    """Show system status."""
    click.echo("System running normally.")