# Typehinting
from typing import List, Tuple

import click
import validators
import datetime
from bunq.sdk.client import Pagination
from bunq.sdk.exception import BunqException
from bunq.sdk.model.generated import endpoint, object_

from buaut import helpers


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
    monetary_account_id: int = ctx.obj.get('monetary_account_id')
    currency: str = ctx.obj.get('currency')

    excludes_list: List[str] = []
    includes_list: List[str] = []

    if includes:
        includes_list = helpers.convert_comma_seperated_to_list(includes)
    if excludes:
        excludes_list = helpers.convert_comma_seperated_to_list(excludes)

    # Get all unsplit events
    # NOTE: Using events since we need to pass event_id to the requestInquiry
    # to get a correct reference
    unsplit_events: List[endpoint.Event] = get_all_unsplit_events(
        monetary_account_id=monetary_account_id,
        includes=includes_list,
        excludes=excludes_list,
        end_date=start)

    if unsplit_events:
        # Create new list of tuples to fill with amounts
        requests: List[Tuple[str, float]] = []
        for event in unsplit_events:
            # Split the bill!
            payment = get_payment_object(event.object_.Payment)

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
                if '%' in a:
                    normalized_percentage: float = float(a) / 100
                    # Calculate amount to request
                    amount: float = amount_to_split * normalized_percentage
                else:
                    amount: float = float(a)

                requests.append((e, amount))

            # Create request batch for payment
            helpers.create_request_batch(
                monetary_account_id=monetary_account_id,
                requests=requests,
                description=str(description),
                currency=currency,
                event_id=event.id_
            )
            # Request sent so empty requests
            requests = []
    else:
        exit(0)


def get_all_unsplit_events(
        monetary_account_id: int, includes: List[str], excludes: List[str], end_date: datetime.datetime
    ) -> List[endpoint.Event]:
    """Get all unsplit payments for a certain account

    Args:
        monetary_account_id (int): Monetary account id

    Returns:
        List[Payment]: List of unsplit bunq payments
    """

    events: List[endpoint.Event] = []
    unsplit_events: List[endpoint.Event] = []

    # Loop until we return
    while True:
        # Check if first iteration (unsplit_payments empty)
        if not events:
            # We will loop over the payments in batches of 50
            pagination = Pagination()
            pagination.count = 50
            params = pagination.url_params_count_only
        else:
            # When there is already a paged request, you can get the next page from it, no need to create it ourselfs:
            try:
                params = events.pagination.url_params_previous_page
            except BunqException:
                break

        # Add parameters to only list for current monetary_account_id
        params['monetary_account_id'] = monetary_account_id
        params['display_user_event'] = 'false'

        # Get events
        events = endpoint.Event.list(
            params=params,
        ).value

        # Filter out all non relevant events
        included_events: List[endpoint.Event] = filter_excluded_events(
            events=events, includes=includes, excludes=excludes)

        for e in included_events:
            if datetime.datetime.strptime(e.created, '%Y-%m-%d %H:%M:%S.%f') < end_date:
                # Break the loop since this is before the end_date
                break

            if e.object_.Payment:
                payment = get_payment_object(e.object_.Payment)

                # Check if it is a sent payment (afschrijving), amount must be negative
                if payment.sub_type == "PAYMENT" and float(payment.amount.value) < 0:
                    # Check if the payment has been split
                    if payment.request_reference_split_the_bill:
                        continue
                    else:
                        # Append payment to list to return
                        unsplit_events.append(e)

        # Return payment in need of splitting
        return unsplit_events


def filter_excluded_events(events: List[endpoint.Event], includes: List[str], excludes: List[str]) -> List[endpoint.Event]:
    """Filter all excluded payments

    Args:
        payments (Payment): Bunq payment object to validate

    Returns:
        List[endpoint.Payment]: List of included payments
    """
    if not includes and not excludes:
        # No need to check just return
        return events

    included_events: List[endpoint.Event] = []
    # Loop payments to filter
    for e in events:
        payment = get_payment_object(e.object_.Payment)
        counterparty = payment.counterparty_alias.label_monetary_account

        # When payment not in excludes it should be included
        if counterparty.iban not in excludes:
            # When includes defined check if included, else just append
            if includes:
                if counterparty.iban in includes:
                    included_events.append(payment)
            else:
                included_events.append(payment)

    return included_events

def get_payment_object(event: endpoint.Payment) -> endpoint.Payment:
    """Workaround for the issue https://github.com/bunq/sdk_python/issues/116

    Args:
        event (endpoint.Payment): Payment object of Event object so incomplete

    Returns:
        endpoint.Payment: Payment object but from the payment endpoint
    """
    payment = endpoint.Payment.get(
       payment_id=event.id_,
       monetary_account_id=event.monetary_account_id
    )
    return payment.value
