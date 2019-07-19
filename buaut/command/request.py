# Typehinting
from typing import Callable, Iterator, Union, Optional, List

import click
import sys
from bunq.sdk.model.generated import endpoint
from bunq.sdk.model.generated.object_ import Pointer, Amount

from buaut import helpers


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
    required=True,
    type=click.STRING
)
@click.option(
    '--currency',
    help='Currency for the requests in an ISO 4217 formatted currency code.',
    type=click.STRING,
    default='EUR'
)
def request(ctx, get: List[tuple], description: str, currency: str):
    """Request on or more user for one or more amount

    Args:
        ctx ([type]): Click object containing the arguments from global
        get ([tuple]): List of users to request from
        description (str): Description for the request
        currency (str): Currency in an ISO 4217 formatted currency code
    """
    # Get global args
    args = ctx.obj.get('args')
    monetary_account_id: str = helpers.get_monetary_account_id(
        type='IBAN', value=args['iban'])

    request_inqueries: List[dict] = []
    total_amount_inquired: int = 0
    for email, amount in get:
      # Add amount to total
      total_amount_inquired += amount
      # Convert to valid Bunq currency string
      amount: str = helpers.convert_to_valid_amount(amount)
      # Create request and append to request_inqueries list
      request_inqueries.append({
          'amount_inquired': Amount(amount, currency),
          'counterparty_alias': Pointer(type_='EMAIL', value=email),
          'description': description,
          'allow_bunqme': True
      })

    # Convert to valid Bunq currency string
    total_amount_inquired: str = helpers.convert_to_valid_amount(
        total_amount_inquired)
    endpoint.RequestInquiryBatch.create(
        request_inquiries=request_inqueries,
        total_amount_inquired=Amount(total_amount_inquired, currency),
        monetary_account_id=monetary_account_id
    )
