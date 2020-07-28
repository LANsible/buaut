# Typehinting
from typing import List, Tuple

import click
import validators
import datetime

from bunq import Pagination
from bunq.sdk.exception.bunq_exception import BunqException
from bunq.sdk.model.generated import endpoint, object_

from buaut import utils


@click.command()
@click.pass_context
@click.option(
    '--get',
    help='Email and percentage/amount to request',
    required=True,
    multiple=True,
    type=(click.STRING, click.STRING)
)
@click.option(
    '--includes',
    help='IBAN numbers to include',
    type=click.STRING
)
@click.option(
    '--excludes',
    help='IBAN numbers to exclude',
    type=click.STRING
)
@click.option(
    '--start',
    help='Date from when should be split',
    # formats are                1970-02-01, 01-02-1970, 02-01-1970, 70-02-01,   01-02-70,   02-01-70
    type=click.DateTime(formats=['%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', '%y-%m-%d', '%d-%m-%y', '%m-%d-%y'])
)
def split(ctx, get: List[Tuple[click.STRING, click.STRING]], includes: click.STRING, excludes: click.STRING, start: datetime):
    """Split payments to certain users

    Args:
        ctx ([type]): Click object containing the arguments from global
        get ([tuple]): List of users to request from
        includes (click.STRING): Comma seperated string containing includes
        excludes (click.STRING): Comma seperated string containing excludes
    """
    monetary_account: int = ctx.obj.get('monetary_account')
    currency: str = ctx.obj.get('currency')

    excludes_list: List[str] = []
    includes_list: List[str] = []

    if includes:
        includes_list = utils.convert_comma_seperated_to_list(includes)
    if excludes:
        excludes_list = utils.convert_comma_seperated_to_list(excludes)

    # Get all events
    # NOTE: Using events since we need to pass event_id to the requestInquiry
    # to get a correct reference
    payment_events: List[endpoint.Event] = utils.get_events(
        monetary_account_id=monetary_account.id_,
        types=["Payment"],
        includes=includes_list,
        excludes=excludes_list,
        end_date=start)

    # Create new list of tuples to fill with amounts
    requests: List[Tuple[str, float]] = []
    for event in payment_events:
        # Get payment object to workaround bug
        payment = utils.get_payment_object(event.object_.Payment)

        # Check if it is a sent payment (afschrijving), amount must be negative
        # Check if the payment has been split already
        if float(payment.amount.value) > 0 or payment.request_reference_split_the_bill:
          continue

        # Convert to positive
        amount_to_split: float = float(payment.amount.value) * -1
        description: dict = {
            'id': payment.id_,
            'from': payment.counterparty_alias.label_monetary_account.display_name,
            'description': payment.description,
            'created': payment.created
        }

        # Create requests based on percentage or amount
        for e, a in get:
            if a.endswith('%'):
                # Remove % and make decimal
                decimal: float = float(a[:-1]) / 100
                # Calculate amount to request
                amount: float = amount_to_split * decimal
            else:
                amount: float = float(a)

            requests.append((e, amount))

        # Create request batch for payment
        utils.create_request_batch(
            monetary_account_id=monetary_account.id_,
            requests=requests,
            description=str(description),
            currency=currency,
            event_id=event.id_
        )
        # Request sent so empty requests
        requests = []
