# Typehinting
from typing import List, Tuple, Optional, Union

import re
import validators
import datetime
import tenacity

from bunq import Pagination
from bunq.sdk.model.generated.endpoint import \
    MonetaryAccountBank, \
    MonetaryAccountJoint, \
    MonetaryAccountLight, \
    MonetaryAccount, \
    Event, \
    Payment, \
    RequestInquiry, \
    RequestInquiryBatch
from bunq.sdk.model.generated.object_ import \
    Amount, \
    RequestReferenceSplitTheBillAnchorObject, \
    Pointer
from bunq.sdk.exception.bunq_exception import BunqException


def get_monetary_account(value_type: str, value: str) -> Union[MonetaryAccountBank,
                                                               MonetaryAccountJoint, MonetaryAccountLight]:
    """Get account with api types

    Args:
        type (str): Possible values: IBAN, EMAIL, PHONE_NUMBER
        value (str): Value of defined type

    Returns:
        int: monetary account id

    Raises:
        ValueError: If match is not found
    """
    pagination = Pagination()
    pagination.count = 25  # maximum of accounts
    monetaryaccount_list = MonetaryAccount.list(
        params=pagination.url_params_count_only).value

    for monetaryaccount in monetaryaccount_list:
        account = monetaryaccount.MonetaryAccountBank or \
            monetaryaccount.MonetaryAccountJoint or \
            monetaryaccount.MonetaryAccountLight or \
            monetaryaccount.MonetaryAccountSavings
        for alias in account.alias:
            if alias.type_ == value_type and alias.value == value:
                return account

    raise ValueError

@tenacity.retry(wait=tenacity.wait_fixed(2))
def get_payments(monetary_account_id: int, includes: Optional[List[str]],
                 excludes: Optional[List[str]], start_date: Optional[datetime.datetime], end_date: Optional[datetime.datetime]) -> List[Payment]:
    """Get events for a certain account

    Args:
        monetary_account_id (int): Monetary account id
        includes (List[str]): IBAN number to include
        excludes (List[str]): IBAN numbers to exclude
        start_date (datetime.datetime): Date to start looking for payments
        end_date (datetime.datetime): Date to stop looking for payments

    Returns:
        List[Event]: List of events
    """

    events: List[Payment] = []
    result: List[Payment] = []

    try:
        # Loop until we raise or return
        while True:
            # Check if first iteration (unsplit_payments empty)
            if not events:
                # We will loop over the payments in batches of 200
                pagination = Pagination()
                pagination.count = 200
                params = pagination.url_params_count_only
            else:
                # TODO: Fix this, this does not seem to work
                # BunqException('Could not generate previous page URL params: there is no previous page.',)

                # When there is already a paged request, you can get the next page from it, no need to create it ourselfs:
                try:
                    params = pagination.url_params_previous_page
                except BunqException:
                    # Break the loop, there is no more to process
                    raise StopIteration

            # Get events
            payments = Payment.list(
                params=params,
                monetary_account_id=monetary_account_id
            ).value

            # Filter out all non relevant events
            payments = _filter_created_date(
                events=payments, start_date=start_date, end_date=end_date)
            return _filter_excluded_payments(payments=payments, includes=includes, excludes=excludes)


    except StopIteration:
        return result


def convert_to_pointer(input: str) -> Pointer:
    """Convert input to Pointer

    Args:
        input (str): email, iban or phonenumber

    Returns:
        Pointer: converted input
    """
    # Split since iban is passed as 'NL92BUNQ12445345,T Test'
    value = convert_comma_seperated_to_list(input)

    # Determine type and return
    if validators.email(value[0]):
        return Pointer(type_="EMAIL", value=value[0])
    elif validators.iban(value[0]):
        return Pointer(type_="IBAN", value=value[0], name=value[1])
    # TODO: implement phonenumber validation in validators
    elif value[0][1:].isdigit():  # removes + sign from phonenumber
        return Pointer(type_="PHONE_NUMBER", value=value[0])
    else:
        # TODO: Create some logging class and exit with message
        print("No valid API Type")
        exit(1)


def convert_to_amount(amount, currency: str) -> Amount:
    """Convert any datatype to a Amount object

    Args:
        amount (any): Amount to convert

    Returns:
        str: Amount in valid currency string
    """
    # Source: https://stackoverflow.com/a/6539677
    return Amount("{0:.2f}".format(amount), currency)


def convert_comma_seperated_to_list(string: str) -> List[str]:
    """Convert comma seperated string to list

    Args:
        string (str): Comma seperated string to split

    Returns:
        List: List contain the items of the string
    """
    # Source: https://stackoverflow.com/a/12760144
    pattern = re.compile(r"^\s+|\s*,\s*|\s+$")
    return pattern.split(string)

@tenacity.retry(wait=tenacity.wait_fixed(2))
def create_request_batch(monetary_account_id: int, requests: List[Tuple[str, float]], description: str, currency: str):
    """Create request batch from a list of requests

    Args:
        monetary_account_id (int): Account id where the requests are made from
        requests (List[tuple]): List of tuples containing destination and amount
        description (str): Description for the requests
        currency (str): Currency for the requests in an ISO 4217 formatted currency code
    """
    request_inqueries: List[dict] = []
    total_amount_inquired: float = 0

    for d, a in requests:
        # Add amount to total
        total_amount_inquired += a
        # Create request and append to request_inqueries list
        request = RequestInquiry(
            amount_inquired=convert_to_amount(a, currency),
            counterparty_alias=convert_to_pointer(d),
            description=description,
            allow_bunqme=True
        )
        # Add request to list
        request_inqueries.append(request)

    # Send the requests to the API to create the requests batch
    RequestInquiryBatch.create(
        request_inquiries=request_inqueries,
        total_amount_inquired=convert_to_amount(
            total_amount_inquired, currency),
        monetary_account_id=monetary_account_id
    )

@tenacity.retry(wait=tenacity.wait_fixed(2))
def create_payment(monetary_account_id: int, amount: Amount, counterparty_alias: Pointer, description: str):
    Payment.create(
        monetary_account_id=monetary_account_id,
        amount=amount,
        counterparty_alias=counterparty_alias,
        description=description,
    )


def _filter_excluded_payments(payments: List[Payment], includes: Optional[List[str]], excludes: Optional[List[str]]
                              ) -> List[Payment]:
    """Filter all excluded payments

    Args:
        payments (Payment): Bunq payment object to validate

    Returns:
        List[Payment]: List of included payments
    """
    if not includes and not excludes:
        # No need to check just return
        return payments

    result: List[Payment] = []
    # Loop payments to filter
    for payment in payments:
        counterparty = payment.counterparty_alias.label_monetary_account

        # When payment not in excludes it should be included
        if counterparty.iban not in excludes:
            # When includes defined check if included, else just append
            if includes:
                if counterparty.iban in includes:
                    result.append(payment)
            else:
                result.append(payment)

    return result


def _filter_created_date(events: List[Payment], start_date: datetime.datetime, end_date: datetime.datetime) -> List[Payment]:
    """Filter Bunq object on created date

    Args:
        events (List[Payment]): List of object to filter
        start_date (datetime.datetime):
        end_date (datetime.datetime):

    Returns:
        List[Payment]: [description]
    """
    if not start_date and not end_date:
        # No need to check just return
        return events

    result: List[Payment] = []
    # Loop objects to filter
    for event in events:
        # example '2020-09-04 13:34:59.712731'
        date: datetime = datetime.datetime.strptime(
            event.created, "%Y-%m-%d %H:%M:%S.%f")

        # When payment not in excludes it should be included
        if date <= start_date and date > end_date:
            result.append(event)

    return result
