# Typehinting
from typing import List, Tuple

import click
import validators
from bunq.sdk.client import Pagination
from bunq.sdk.exception import BunqException
from bunq.sdk.model.generated import endpoint
from bunq.sdk.model.generated.object_ import Pointer, Amount
from pprint import pprint

from buaut import helpers


@click.command()
@click.pass_context
@click.option(
    '--get',
    help='Email and percentage/amount to request',
    required=True,
    multiple=True,
    type=(str, str)
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
def split(ctx, get: List[Tuple[str, float]], includes: str, excludes: str):
    """Split payments to certain users

    Args:
        ctx ([type]): Click object containing the arguments from global
        get ([tuple]): List of users to request from
        includes (str): Comma seperated string containing includes
        excludes (str): Comma seperated string containing excludes
    """
    monetary_account_id: int = ctx.obj.get('monetary_account_id')
    currency: str = ctx.obj.get('currency')

    excludes_list: List[str] = []
    includes_list: List[str] = []

    if includes:
        includes_list = helpers.comma_seperated_string_to_list(includes)
    if excludes:
        excludes_list = helpers.comma_seperated_string_to_list(excludes)

    # Get all unsplit events
    # NOTE: Using events since we need to pass event_id to the requestInquiry
    # to get a correct reference
    unsplit_events: List[endpoint.Event] = get_all_unsplit_events(
        monetary_account_id)

    # Filter out all non relevant events
    included_events: List[endpoint.Event] = filter_excluded_events(
        events=unsplit_events, includes=includes_list, excludes=excludes_list)

    if included_events:
        # Create new list of tuples to fill with amounts
        requests: List[Tuple[str, float]] = []
        for event in included_events:
            # Split the bill!
            payment = event.object_.Payment

            # Convert to positive
            amount_to_split: float = float(payment.amount.value) * -1
            description: dict = {
                'id': payment.id_,
                'from': payment.counterparty_alias.label_monetary_account.display_name,
                'description': payment.description,
                'created': payment.created
            }

            for email, percentage in get:
                normalized_percentage: float = float(percentage) / 100
                # Calculate amount to request
                amount: float = amount_to_split * normalized_percentage
                requests.append((email, amount))

            # Create request batch for payment
            helpers.create_request_batch(
                monetary_account_id=monetary_account_id,
                requests=requests,
                description=str(description),
                currency=currency,
                event_id_field_for_request=event._id
            )
            # Request sent so empty requests
            requests = []
    else:
        exit(0)


def get_all_unsplit_events(monetary_account_id: int) -> List[endpoint.Event]:
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
            # We will loop over the payments in baches of 50
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

        for event in events:
            if event.object_.Payment:
                payment = event.object_.Payment
                # Check if it is a sent payment (afschrijving), amount must be negative
                # TODO: Include requests (Ann requests groceries)
                if payment.sub_type == "PAYMENT" and float(payment.amount.value) < 0:
                    # Check if the payment has been split
                    if payment.request_reference_split_the_bill:
                        if is_buaut_split_the_bill(payment):
                            # Break loop since this is where we left the last time
                            break
                        else:
                            # Skip payment has been made manually
                            continue

                    # Append payment to list to return
                    unsplit_events.append(event)

        # Return payment in need of splitting
        return unsplit_events


def filter_excluded_events(events: List[endpoint.Event], includes: List[str], excludes: List[str]) -> List[endpoint.Event]:
    """Filter all excluded payments

    Args:
        payments (Payment): Bunq payment object to validate

    Returns:
        List[endpint.Payment]: List of included payments
    """
    if not includes and not excludes:
        # No need to check just return
        return events

    included_events: List[endpoint.Event] = []
    # Loop payments to filter
    for event in events:
        payment = event.object_.Payment
        counterparty = payment.counterparty_alias.label_monetary_account

        # When payment in excludes it should be included
        if counterparty.iban not in excludes:
            # When includes defined check if included, else just append
            if includes:
                if counterparty.iban in includes:
                    included_events.append(payment)
            else:
                included_events.append(payment)

    return included_events


def is_buaut_split_the_bill(payment: endpoint.Payment) -> bool:
    payment.request_reference_split_the_bill
    return False
