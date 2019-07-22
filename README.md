# bunq-automations

```
buaut split --iban --includes "NL12BUNQ123123123,NL12BUNQ123123123" --excludes "NL12BUNQ123123123,NL12BUNQ123123123" --get sugardaddy@bunq.com 10 --get sugardaddy@bunq.com 20
buaut --sandbox --iban=<iban> --api-key=<key> request --get sugardaddy@bunq.com 10 --get sugardaddy@bunq.com 20 --description="Test double user"
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