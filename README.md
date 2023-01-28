# Buaut

A personal project I use to ease budgetting between me and my wife.
We have multiple accounts where we add money to each month in a ratio reflecting our income.
There is also a fixed expenses account (rent, utilities etc) we split monthly on a per payment bases (this is where `split` comes into play)/
My last usecase is a contra-account for an non Bunq savings account. We receive a request to add money to this subaccount and then weekly this
account balance is forwarded to the external saving account with the forward command.


## User documentation

All destinations can be specified with an email, phonenumber or an IBAN:
```
--get sugardaddy@bunq.me 20
--get +31611223344 20
--get "NL43BUNQ1122334455,T User" 20
```

Use the `--help` parameters to view the help for commands like so:
```console
# buaut --help
Usage: buaut [OPTIONS] COMMAND [ARGS]...

   ____                    _
  | __ ) _   _  __ _ _   _| |_
  |  _ \| | | |/ _` | | | | __|
  | |_) | |_| | (_| | |_| | |_
  |____/ \__,_|\__,_|\__,_|\__|

  Buaut are several Bunq automations in a convenient CLI tool.

  Enable autocomplete for Bash (.bashrc):   eval "$(_BUAUT_COMPLETE=source
  buaut)"

  Enable autocomplete for ZSH (.zshrc):   eval "$(_BUAUT_COMPLETE=source_zsh
  buaut)"

Options:
  --iban TEXT          Enter IBAN where to run a function. Can be set as
                       environment variable BUAUT_IBAN  [required]
  --api-key TEXT       Provide the api token for the Bunq API. Can be set as
                       environment variable BUAUT_API_KEY  [required]
  --sandbox            Pass when testing against the Bunq sandbox. Can be set
                       as environment variable BUAUT_SANDBOX
  --currency TEXT      Currency for the requests in an ISO 4217 formatted
                       currency code.  [default: EUR]
  --context-path PATH  File path to save the ApiContext to, must be kept and
                       re-used to avoid problems  [default: buaut.json]
  --version            Show the version and exit.
  --help               Show this message and exit.

Commands:
  forward  Forward payments to other IBAN
  request  Request on or more user for one or more amount
  split    Split payments to certain users works from newest to oldest
```

## Environment variables

The CLI is built with Click and the docs apply to this:
https://click.palletsprojects.com/en/8.1.x/options/#values-from-environment-variables

These variables are available to set as an environment variable
```
BUAUT_API_KEY=ddgfgdffsdfsdsdkfdsfkdshkj9823774234
BUAUT_IBAN=NL98BUNQ1122337744
BUAUT_GET="user1@example.org 20% user2@example.org 80%"
BUAUT_CONTEXT_PATH=/config/context.json
```

## Command examples

### request
```
buaut --iban NL98BUNQ1122337744 request --get user1@example.org "16.50" --get user2@example.org "64" --description "Request amount"
buaut --iban NL98BUNQ1122337744 request --get user1@example.org "20%" --get user2@example.org "80%" --total "100" --description "Split total by percentage"
```

### forward
```
buaut --iban NL98BUNQ1122337744 forward --destination "NL43BUNQ1122334455,T User"
```

### split
```
buaut --iban NL98BUNQ1122337744 split --period monthly --get user1@example.org "20%" --get user2@example.org "80%"
```

## Docker
Needed since /dev/shm ins't mounted as exec
https://github.com/pyinstaller/pyinstaller/issues/4548
```
docker run -t --tmpfs /tmp:exec lansible:buaut
```
