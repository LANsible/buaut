# Typehinting
from typing import List

import validators
import pbr.version
import socket
import click

from buaut import command
from bunq.sdk.context import ApiContext, BunqContext, ApiEnvironmentType

from buaut import helpers


@click.group()
@click.option(
    '--iban',
    envvar='BUAUT_IBAN',
    required=True,
    help='Enter IBAN where to run a function. '
    'Can be set as environment variable BUAUT_IBAN',
    type=click.STRING
)
@click.option(
    '--api-key',
    envvar='BUAUT_API_KEY',
    required=True,
    help='Provide the api token for the Bunq API. '
    'Can be set as environment variable BUAUT_API_KEY',
    type=click.STRING
)
@click.option(
    '--sandbox',
    envvar='BUAUT_SANDBOX',
    is_flag=True,
    help='Pass when testing against the Bunq sandbox. '
    'Can be set as environment variable BUAUT_SANDBOX',
)
@click.option(
    '--currency',
    help='Currency for the requests in an ISO 4217 formatted currency code.',
    type=click.STRING,
    default='EUR',
    show_default=True
)
@click.version_option(version=pbr.version.VersionInfo('buaut'))
@click.pass_context
def main(ctx, iban: str, api_key: str, sandbox: bool, currency: str):
    """
    \b
     ____                    _
    | __ ) _   _  __ _ _   _| |_
    |  _ \| | | |/ _` | | | | __|
    | |_) | |_| | (_| | |_| | |_
    |____/ \__,_|\__,_|\__,_|\__|

    Buaut are several Bunq automations in a
    convenient CLI tool.

    Enable autocomplete for Bash (.bashrc):
      eval "$(_BUAUT_COMPLETE=source buaut)"

    Enable autocomplete for ZSH (.zshrc):
      eval "$(_BUAUT_COMPLETE=source_zsh buaut)"
    """
    # Set Bunq context
    context = ApiEnvironmentType.SANDBOX if sandbox \
        else ApiEnvironmentType.PRODUCTION

    # Setup Bunq authentication
    api_context = ApiContext(context, api_key,
                             socket.gethostname())
    api_context.ensure_session_active()

    # Load api context into BunqContext used for subsequent calls
    BunqContext.load_api_context(api_context)

    if validators.iban(iban):
        try:
            # Set monetary_account_id
            monetary_account_id: int = helpers.get_monetary_account_id(
                value_type='IBAN', value=iban)
        except:
            # TODO: Exit nicely
            exit(1)
    else:
        # TODO: Exit nicely
        exit(1)

    # Append to ctx object to have available in commands
    ctx.obj: dict = {}
    ctx.obj['args']: dict = {}
    ctx.obj['args']['iban']: str = iban
    ctx.obj['args']['api_key']: str = api_key
    ctx.obj['monetary_account_id']: int = monetary_account_id
    ctx.obj['currency']: str = currency


main.add_command(command.request.request)
main.add_command(command.split.split)
