# Typehinting
from typing import List, Tuple

import click

from bunq.sdk.model.generated import endpoint

from buaut import utils


@click.command()
@click.pass_context
@click.option(
    '--destination',
    help='Destination where to forward to',
    required=True,
    type=click.STRING
)
@click.option(
    '--description',
    help='Description for the payment',
    type=click.STRING,
    default='Made by Buaut'
)
def forward(ctx, destination: str, description: str):
    """Forward payments to other IBAN

    Args:
        ctx ([type]): Click object containing the arguments from global
        get ([tuple]): List of users to request from
        description (str): Description for the request
    """
    monetary_account: int = ctx.obj.get('monetary_account')
    utils.create_payment(
        monetary_account_id=monetary_account.id_,
        amount=monetary_account.balance,
        counterparty_alias=utils.convert_to_pointer(destination),
        description=description
    )
