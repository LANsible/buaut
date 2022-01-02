# Typehinting
from typing import List, Tuple

import click
from buaut import utils


@click.command()
@click.pass_context
@click.option(
    '--get',
    help='Destination and amount (xx.xx) to request',
    required=True,
    multiple=True,
    type=(str, float)
)
@click.option(
    '--description',
    help='Description for the request',
    required=False,
    default= "Made by Buaut",
    type=click.STRING
)
def request(ctx, get: List[Tuple[str, float]], description: str):
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
