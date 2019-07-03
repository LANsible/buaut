import click

from gip import command


@click.group()
@click.option(
    '--iban',
    envvar='BAUT_IBAN',
    default=False,
    help='Enter IBAN where to run a function \
        Can be set as environment variable BAUT_IBAN'
)
@click.option(
    '--api-key',
    envvar='BAUT_API_KEY',
    default=False,
    help='Provide the api token for the Bunq API \
        Can be set as environment variable BAUT_API_KEY'
)
@click.version_option(version='0.0.1')
@click.pass_context
def main(ctx, iban, api_key):
    """
    \b
     ___            _   
    | _ ) __ _ _  _| |_ 
    | _ \/ _` | || |  _|
    |___/\__,_|\_,_|\__|
                  
    Baut are several bunq automations in a 
    convenient CLI tool.
    
    Enable autocomplete for Bash (.bashrc):
      eval "$(_GIP_COMPLETE=source gip)"

    Enable autocomplete for ZSH (.zshrc):
      eval "$(_GIP_COMPLETE=source_zsh gip)"
    """
    ctx.obj = {}
    ctx.obj['args'] = {}
    ctx.obj['args']['iban'] = debug
    ctx.obj['args']['api_key'] = gitlab_token


main.add_command(command.install.install)
