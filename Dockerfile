FROM alpine:3.10 as builder

RUN apk add --no-cache \
    build-base \
    git \
    python3-dev

COPY . /buaut
RUN pip3 install --upgrade pip pyinstaller && \
    pip3 install -r /buaut/requirements.txt
    pip3 install -e /buaut

RUN pyinstaller --onefile /usr/bin/buaut
