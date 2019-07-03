import socket
import yaml
from bunq.sdk.client import Pagination
from bunq.sdk.context import ApiContext, BunqContext, ApiEnvironmentType
from bunq.sdk.model.generated import endpoint
from bunq.sdk.model.generated.object_ import Pointer, Amount

# ENVIRONMENT_TYPE = "sandbox"
API_KEY = "807befa3a230a696411688ace8da721da26b0a2979f440e0d30124dbc4c0fb09"
DEVICE_DESCRIPTION = "buaut"
ACCOUNT="NL21BUNQ9900274229"
SPLIT = {
  # 'NL49BUNQ9900237544': 30,
  'NL65BUNQ9900000188': 70
}
EXCLUDES = []
HOSTNAME = socket.gethostname()

def main():
  api_context = ApiContext(ApiEnvironmentType.SANDBOX, API_KEY,
    HOSTNAME)
  api_context.ensure_session_active()
  
  # Load api context into BunqContext used for subsequent calls
  BunqContext.load_api_context(api_context)
  
  user = endpoint.User.get().value.get_referenced_object()
  accounts = get_all_monetary_account_active(count=10)
  payments = get_all_unsplit_payments()


def get_all_monetary_account_active(count):
    """
    :type count: int
    :rtype: list[endpoint.MonetaryAccountBank]
    """

    pagination = Pagination()
    pagination.count = count

    all_monetary_account_bank = endpoint.MonetaryAccountBank.list(
        pagination.url_params_count_only).value
    all_monetary_account_bank_active = []

    for monetary_account_bank in all_monetary_account_bank:
        if monetary_account_bank.status == 'ACTIVE':
            all_monetary_account_bank_active.append(monetary_account_bank)

    return all_monetary_account_bank_active

def get_all_payments(count):
    """
    :type count: int
    :rtype: list[Payment]
    """

    pagination = Pagination()
    pagination.count = count

    all_payments = endpoint.Payment.list(
      params=pagination.url_params_count_only).value

    return all_payments

def get_all_unsplit_payments():
    """Get all unsplit payments for a certain account
    """
    
    unsplit_payments = None
    monetary_account_id = get_monetary_account_id(type='IBAN', value=ACCOUNT)

    # Loop until we break the loop
    while True:
      if unsplit_payments == None:
          # We will loop over the payments in baches of 1
          pagination = Pagination()
          pagination.count = 10
          params = pagination.url_params_count_only

      else:
          # When there is already a paged request, you can get the next page from it, no need to create it ourselfs:
          try:
              params = events.pagination.url_params_previous_page
          except BunqException:
              break

      # payments = endpoint.Payment.list(
      #     params=params).value
      params['monetary_account_id'] = monetary_account_id
      params['display_user_event'] = 'false'
      events = endpoint.Event.list(
          params=params,
          ).value
      print()
      for event in events:
        if event.object_.Payment:
          payment = event.object_.Payment
          if payment.request_reference_split_the_bill \
              and not is_excluded(payment):
            # Break loop since this is where we left the last time
            break
          else:
            # Split the bill!
            if float(payment.amount.value) > 0:
              continue  # not a afschrijving
            amount_to_split = float(payment.amount.value) * -1  # Convert to positive
            description = {
              'id': payment.id_,
              'from': payment.counterparty_alias.label_monetary_account.display_name,
              'description': payment.description,
              'created': payment.created
            }
            request_inqueries = []
            for iban,percentage in SPLIT.items():
              # Calculate amount and format (https://stackoverflow.com/a/6539677)
              amount = "{0:.2f}".format(amount_to_split * (percentage / 100))
              request_inqueries += RequestInquiry (
                allow_bunqme=True,
                amount_inquired=Amount(amount, payment.amount.currency),
                counterparty_alias=Pointer(type_='IBAN', value=iban, name=iban),
                description=yaml.dump(description),
                monetary_account_id=monetary_account_id)
            
            endpoint.RequestInquiryBatch.create(
              request_inqueries=request_inqueries
            )

def is_excluded(payment):
  """Find out if a payment is excluded
  
  :param payment: Bunq payment
  :type payment: Payment
  :return: Boolean of the payment is excluded
  :rtype: bool
  """
  counterparty = payment.counterparty_alias.label_monetary_account
  return counterparty.display_name in EXCLUDES or \
          counterparty.iban in EXCLUDES


def get_monetary_account_id(type, value):
  """Get account_id with api types
  
  :param type: Possible values: IBAN, EMAIL, PHONE_NUMBER
  :type type: str
  :param value: value of defined type
  :type value: str
  :return: monetary account id
  :rtype: ints
  """
  pagination = Pagination()
  pagination.count = 25
  monetaryaccount_list = endpoint.MonetaryAccount.list(
    params=pagination.url_params_count_only).value
  
  for monetaryaccount in monetaryaccount_list:
    for alias in monetaryaccount.MonetaryAccountBank.alias:
      if alias.type_ == type and alias.value == value:
        return monetaryaccount.MonetaryAccountBank.id_

if __name__ == '__main__':
  main()
