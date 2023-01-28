## Release
```
pip install -r build-requirements.txt
make -f build/Makefile clean
make -f build/Makefile build
make -f build/Makefile push
```

## Setup dev
```
pip install -r requirements.txt
python setup.py develop
export BUAUT_IBAN=<iban>
export BUAUT_API_KEY=<key>
```
