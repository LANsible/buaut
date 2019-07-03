import click

@click.command()
@click.pass_context
@click.option(
    '--includes',
    help='Requirements file to install',
    type=click.Path(
        exists=True,
    )
)
def split(ctx, upgrade, requirements):
