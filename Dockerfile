FROM ubuntu:bionic as builder

RUN apt-get update && \
    apt-get install -y \
      python3-dev \
      python3-pip \
      build-essential \
      ca-certificates \
      # Needed for pbr version since not released to pypi
      git \
      # Optional for pyinstaller
      upx \
      # Required for staticx
      patchelf

COPY . /buaut
RUN pip3 install -r /buaut/requirements.txt && \
    pip3 install pyinstaller staticx && \
    pip3 install -e /buaut

WORKDIR /buaut
RUN pyinstaller --strip --onefile /usr/local/bin/buaut && \
    staticx dist/buaut dist/buaut_static

# Scratchy yes yes
FROM scratch
ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

# Add locale otherwise Click does not work:
# https://click.palletsprojects.com/en/7.x/python3/
COPY --from=builder /usr/lib/locale/C.UTF-8 /usr/lib/locale/C.UTF-8
# Add ssl certificates
COPY --from=0 /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
# Add compiled binary
COPY --from=builder /buaut/dist/buaut_static /buaut

ENTRYPOINT [ "/buaut" ]
CMD [ "--help" ]