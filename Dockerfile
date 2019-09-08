# Using non alpine for glibc which pyinstaller needs
FROM ubuntu:disco as builder

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
      patchelf \
      # Smaller better binaries:
      # https://github.com/JonathonReinhart/staticx#from-source
      musl-tools

COPY . /buaut
RUN pip3 install -r /buaut/requirements.txt && \
    pip3 install pyinstaller scons && \
    pip3 install -e /buaut && \
    # Needed for scons:
    # /usr/bin/env: python: No such file or directory
    update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    CC=/usr/bin/musl-gcc pip3 install https://github.com/JonathonReinhart/staticx/archive/master.zip

WORKDIR /buaut
RUN pyinstaller --strip --onefile /usr/local/bin/buaut && \
    staticx --strip -l /lib/x86_64-linux-gnu/libnss_dns.so.2 -l /lib/x86_64-linux-gnu/libresolv.so.2 dist/buaut dist/buaut_static

# Scratchy yes yes
FROM scratch
ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

# Add locale otherwise Click does not work:
# https://click.palletsprojects.com/en/7.x/python3/
COPY --from=builder /usr/lib/locale/C.UTF-8 /usr/lib/locale/C.UTF-8

COPY --from=builder /etc/passwd /etc/group /etc/
# Add ssl certificates
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
# Add compiled binary
COPY --from=builder /buaut/dist/buaut_static /buaut

ENTRYPOINT [ "/buaut" ]
CMD [ "--help" ]