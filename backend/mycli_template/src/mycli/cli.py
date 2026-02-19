import click
from .commands import process, status

@click.group()
@click.version_option("0.1.0")
def main():
    """MyCLI - Sample CLI Tool"""
    pass

main.add_command(process.process_cmd)
main.add_command(status.status_cmd)