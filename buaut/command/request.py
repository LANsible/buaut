# Typehinting
from typing import List, Tuple

import click

from bunq.sdk.model.generated import endpoint
from bunq.sdk.model.generated.object_ import Pointer, Amount

from buaut import utils


@click.command()
@click.pass_context
@click.option(
    '--get',
    help='Email and amount (xx.xx) to request',
    required=True,
    multiple=True,
    type=(str, float)
)
@click.option(
    '--description',
    help='Description for the request',
    required=False,
    type=click.STRING
)
def request(ctx, get: List[Tuple[str, float]], description: str = "Made by Buaut"):
    """Request on or more user for one or more amount

    Args:
        ctx ([type]): Click object containing the arguments from global
        get ([tuple]): List of users to request from
        description (str): Description for the request
    """
    monetary_account: int = ctx.obj.get('monetary_account')
    currency: str = ctx.obj.get('currency')

    utils.create_request_batch(
        monetary_account_id=monetary_account.id_,
        requests=get,
        description=description,
        currency=currency
    )
