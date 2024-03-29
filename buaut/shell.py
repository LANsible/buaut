# Typehinting
from typing import List

import validators
import pbr.version
import socket
import click

from buaut import command
from bunq.sdk.exception.bunq_exception import BunqException
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq.sdk.context.api_environment_type import ApiEnvironmentType

from buaut import utils


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
    help='Pass when testing against the Bunq sandbox.'
    'Can be set as environment variable BUAUT_SANDBOX',
)
@click.option(
    '--currency',
    help='Currency for the requests in an ISO 4217 formatted currency code.',
    type=click.STRING,
    default='EUR',
    show_default=True
)
@click.option(
    '--context-path',
    envvar='BUAUT_CONTEXT_PATH',
    help='File path to save the ApiContext to, must be kept and re-used to avoid problems'
    'Can be set as environment variable BUAUT_CONTEXT_PATH',
    type=click.Path(),
    default='buaut.json',
    show_default=True
)
@click.version_option(version=pbr.version.VersionInfo('buaut'))
@click.pass_context
def main(ctx, iban: str, api_key: str, sandbox: bool, currency: str, context_path: click.Path):
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
    try:
        api_context = ApiContext.restore(path=str(context_path))
    except:
        api_context = ApiContext.create(context, api_key, 'buaut')

    api_context.ensure_session_active()
    api_context.save(path=str(context_path))

    # Load api context into BunqContext used for subsequent calls
    BunqContext.load_api_context(api_context)

    if validators.iban(iban):
        try:
            # Set monetary_account
            monetary_account: int = utils.get_monetary_account(
                value_type='IBAN', value=iban)
        except:
            # TODO: Exit nicely
            exit(1)
    else:
        # TODO: Exit nicely
        exit(1)

    # Append to ctx object to have available in commands
    ctx.obj = {}
    ctx.obj['args'] = {}
    ctx.obj['args']['iban'] = iban
    ctx.obj['args']['api_key'] = api_key
    ctx.obj['monetary_account'] = monetary_account
    ctx.obj['currency'] = currency


main.add_command(command.request.request)
main.add_command(command.split.split)
main.add_command(command.forward.forward)
