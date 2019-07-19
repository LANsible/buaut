from bunq.sdk.client import Pagination
from bunq.sdk.model.generated import endpoint


def get_monetary_account_id(type: str, value: str) -> int:
  """Get account_id with api types

  Args:
      type (str): Possible values: IBAN, EMAIL, PHONE_NUMBER
      value (str): Value of defined type

  Returns:
      int: monetary account id
  """
  pagination = Pagination()
  pagination.count = 25
  monetaryaccount_list = endpoint.MonetaryAccount.list(
      params=pagination.url_params_count_only).value

  for monetaryaccount in monetaryaccount_list:
    for alias in monetaryaccount.MonetaryAccountBank.alias:
      if alias.type_ == type and alias.value == value:
        return monetaryaccount.MonetaryAccountBank.id_


def convert_to_valid_amount(amount: any) -> str:
    """Convert any datatype to a valid amount (xx.xx)

    Args:
        amount (any): Amount to convert

    Returns:
        str: Amount in valid currency string
    """
    # Format trick from: https://stackoverflow.com/a/6539677
    return "{0:.2f}".format(amount)
