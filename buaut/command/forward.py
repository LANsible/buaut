# Typehinting
from typing import List, Tuple

import click

from bunq.sdk.model.generated import endpoint, object_

from buaut import utils


@click.command()
@click.pass_context
@click.option(
    '--destination',
    help='IBAN and name where to forward to',
    required=True,
    type=(str, str)
)
@click.option(
    '--description',
    help='Description for the payment',
    type=click.STRING,
    default='Made by Buaut'
)
def forward(ctx, destination: List[Tuple[click.STRING, click.STRING]], description: str):
    """Forward payments to other IBAN

    Args:
        ctx ([type]): Click object containing the arguments from global
        get ([tuple]): List of users to request from
        description (str): Description for the request
    """
    monetary_account: int = ctx.obj.get('monetary_account')
    endpoint.Payment.create(
      amount=monetary_account.balance,
      counterparty_alias=object_.Pointer(type_='IBAN', value=destination[0], name=destination[1]),
      description=description,
    )
