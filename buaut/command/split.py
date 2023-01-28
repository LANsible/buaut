# Typehinting
from typing import List, Tuple

import click
import validators
import datetime
import dateutil.relativedelta

from bunq.sdk.model.generated.endpoint import Payment  # just here for the typehint

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
    '--period',
    help='How far to split back in time from the start parameter',
    required=True,
    type=click.Choice(['daily', 'weekly', 'monthly'], case_sensitive=False)
)
@click.option(
    '--start',
    help='Day to start the period from in YYYY-MM-DD format, defaults to today',
    # formats are                1970-02-01, 70-02-01
    type=click.DateTime(formats=['%Y-%m-%d', '%y-%m-%d']),
    default=str(datetime.date.today())
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
def split(ctx, get: List[Tuple[click.STRING, click.STRING]], period: click.Choice, start: click.DateTime,
    includes: click.STRING, excludes: click.STRING):
    """Split payments to certain users works from newest to oldest

    Args:
        ctx ([type]): Click object containing the arguments from global
        get ([tuple]): List of users to request from
        period (click.STRING): How far to split back in time (monthly, weekly, daily)
        start (click.DateTime): Day to start the period from, if undefined uses today
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

    if period == "daily":
        end_date = start - dateutil.relativedelta.relativedelta(days=1)
    elif period == "weekly":
        end_date = start - dateutil.relativedelta.relativedelta(weeks=1)
    elif period == "monthly":
        end_date = start - dateutil.relativedelta.relativedelta(months=1)
    else:
        # TODO: Exit nicely
        exit(1)

    # Get all events
    # NOTE: Using events since we need to pass event_id to the requestInquiry
    # to get a correct reference
    payments: List[Payment] = utils.get_payments(
        monetary_account_id=monetary_account.id_,
        includes=includes_list,
        excludes=excludes_list,
        start_date=start,
        end_date=end_date)

    # Create new list of tuples to fill with amounts
    requests: List[Tuple[str, float]] = []
    for payment in payments:
        # Check if it is a sent payment (afschrijving), amount must be negative
        # Check if the payment has been split already
        # TODO: request_reference_split_the_bill is currently None even when there has been a split
        # https://github.com/bunq/sdk_python/issues/122
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
            event_id=payment.id_
        )
        # Request sent so empty requests
        requests = []
