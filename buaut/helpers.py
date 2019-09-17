# Typehinting
from typing import List, Tuple

import re
import validators

from bunq.sdk.client import Pagination
from bunq.sdk.model.generated import endpoint
from bunq.sdk.model.generated.object_ import Pointer, Amount


def get_monetary_account_id(value_type: str, value: str) -> int:
    """Get account_id with api types

    Args:
        type (str): Possible values: IBAN, EMAIL, PHONE_NUMBER
        value (str): Value of defined type

    Returns:
        int: monetary account id

    Raises:
        ValueError: If match is not found
    """
    pagination = Pagination()
    pagination.count = 25
    monetaryaccount_list = endpoint.MonetaryAccount.list(
        params=pagination.url_params_count_only).value

    for monetaryaccount in monetaryaccount_list:
        account = monetaryaccount.MonetaryAccountBank or \
                    monetaryaccount.MonetaryAccountJoint or \
                    monetaryaccount.MonetaryAccountLight or \
                    monetaryaccount.MonetaryAccountSavings
        for alias in account.alias:
            if alias.type_ == value_type and alias.value == value:
                return account.id_

    raise ValueError


def convert_to_valid_amount(amount) -> str:
    """Convert any datatype to a valid amount (xx.xx)

    Args:
        amount (any): Amount to convert

    Returns:
        str: Amount in valid currency string
    """
    # Source: https://stackoverflow.com/a/6539677
    return "{0:.2f}".format(amount)


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


def create_request_batch(monetary_account_id: int, requests: List[Tuple[str, float]], description: str, currency: str, event_id_field_for_request: int=None):
    """Create request batch from a list of requests

    Args:
        monetary_account_id (int): Account id where the requests are made from
        requests (List[tuple]): List of tuples containing email and amount
        description (str): [description]
        currency (str): [description]
    """
    request_inqueries: List[dict] = []
    total_amount_inquired: float = 0

    for email, amount in requests:
        # Check if valid email
        # TODO: Create some logging class and exit with message
        if not validators.email(email):
            exit(1)

        # Add amount to total
        total_amount_inquired += amount
        # Create request and append to request_inqueries list
        request = endpoint.RequestInquiry(
            amount_inquired=Amount(convert_to_valid_amount(amount), currency),
            counterparty_alias=Pointer(type_='EMAIL', value=email),
            description=description,
            allow_bunqme=True,
            event_id=event_id_field_for_request
        )

        # Add request to list
        request_inqueries.append(request)


    # Convert to valid Bunq currency string
    total_amount_inquired_string: str = convert_to_valid_amount(
        total_amount_inquired)

    # Send the requests to the API to create the requests batch
    endpoint.RequestInquiryBatch.create(
        request_inquiries=request_inqueries,
        total_amount_inquired=Amount(total_amount_inquired_string, currency),
        monetary_account_id=monetary_account_id
    )
