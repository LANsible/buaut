# bunq-automations

```
buaut split --iban --includes --excludes --users=wilmar94do@hotmail.com,rosefull@gmail.com --percentages=60,40
buaut --sandbox --iban=<iban> --api-key=<key> request --request sugardaddy@bunq.com 10 --request sugardaddy@bunq.com 20 --description="Test double user"
```

## Release
```
pip install -r build-requirements.txt
make -f build/Makefile clean
make -f build/Makefile build
make -f build/Makefile push
```

## Setup dev
```
python setup.py develop
export BUAUT_IBAN=<iban>
export BUAUT_API_KEY=<key>
```