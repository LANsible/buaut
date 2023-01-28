# Typehinting
from typing import List, Tuple

import click
from buaut import utils


@click.command()
@click.pass_context
@click.option(
    '--get',
    envvar='BUAUT_GET',
    help='Destination and amount/percentage to request'
    'Can be set as environment variable BUAUT_GET',
    required=True,
    multiple=True,
    type=(click.STRING, click.STRING)
)
@click.option(
    '--total',
    help='Total to request when --get is a percentage',
    type=(float)
)
@click.option(
    '--description',
    help='Description for the request',
    required=False,
    default= "Made by Buaut",
    type=click.STRING
)
def request(ctx, get: List[Tuple[click.STRING, click.STRING]], total: float, description: str):
    """Send a request to one or more Bunq users

    Args:
        ctx ([type]): Click object containing the arguments from global
        get ([tuple]): List of users to request from
        description (str): Description for the request
    """
    monetary_account: int = ctx.obj.get('monetary_account')
    currency: str = ctx.obj.get('currency')

    # Create new list of tuples to fill with amounts
    requests: List[Tuple[str, float]] = []
    # Create requests based on percentage or amount
    for e, a in get:
        if a.endswith('%'):
            # total required when percentage is given
            if not total:
                # TODO: Exit nicely
                exit(1)

            # Remove % and make decimal
            decimal: float = float(a[:-1]) / 100
            # Calculate amount to request
            amount: float = total * decimal
        else:
            amount: float = float(a)

        requests.append((e, amount))

    utils.create_request_batch(
        monetary_account_id=monetary_account.id_,
        requests=requests,
        description=description,
        currency=currency
    )
