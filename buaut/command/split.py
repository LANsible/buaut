# Typehinting
from typing import List, Tuple

import click
import validators
from bunq.sdk.client import Pagination
from bunq.sdk.exception import BunqException
from bunq.sdk.model.generated import endpoint
from bunq.sdk.model.generated.object_ import Pointer, Amount, Payment

from buaut import helpers

# Global variables
INCLUDES: List[str] = []
EXCLUDES: List[str] = []


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
  excludes: List[str] = helpers.comma_seperated_string_to_list(excludes)
  includes: List[str] = helpers.comma_seperated_string_to_list(includes)
  monetary_account_id: int = ctx.obj.get('monetary_account_id')

  unsplit_payments = get_all_unsplit_payments(monetary_account_id)
  # Split the bill!
  if float(payment.amount.value) > 0:
    continue  # not a afschrijving
  # Convert to positive
  amount_to_split = float(payment.amount.value) * -1
  description = {
      'id': payment.id_,
      'from': payment.counterparty_alias.label_monetary_account.display_name,
      'description': payment.description,
      'created': payment.created
  }
  request_inqueries = []
  for iban, percentage in SPLIT.items():
    # Calculate amount and format (https://stackoverflow.com/a/6539677)
    amount = "{0:.2f}".format(amount_to_split * (percentage / 100))


def get_all_unsplit_payments(monetary_account_id: int) -> List[Payment]:
    """Get all unsplit payments for a certain account

    Args:
        monetary_account_id (int): Monetary account id

    Returns:
        List[Payment]: List of unsplit bunq payments
    """

    unsplit_payments: List[Payment] = []

    # Loop until we break the loop
    while True:
      # Check if first iteration (unsplit_payments empty)
      if unsplit_payments:
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
          if payment.request_reference_split_the_bill \
                  and is_included(payment)
                  and is_buaut_split_the_bill:
            # Break loop since this is where we left the last time
            break

      # Return payment in need of splitting
      return unsplit_payments


def is_included(payment: Payment) -> bool:
  """Find out if a payment is included

  Args:
      payment (Payment): Bunq payment object to validate

  Returns:
      bool: If payment is included in this batch
  """
  counterparty = payment.counterparty_alias.label_monetary_account

  # When includes is defined check on includes to, else just check excludes
  if INCLUDES:
    return counterparty.iban in INCLUDES and \
        counterparty.iban not in EXCLUDES
  else:
    return counterparty.iban not in EXCLUDES
