#######################################################################################################################
# Package binary with Pyinstaller
#######################################################################################################################
# Using non alpine for glibc which pyinstaller needs
FROM alpine:3.15 as builder

# Add unprivileged user
RUN echo "buaut:x:1000:1000:buaut:/:" > /etc_passwd

RUN apk add --no-cache \
      python3-dev \
      py3-pip \
      build-base \
      # Needed for pbr version since not released to pypi
      git \
      # Needed for both staticx and pyinstaller
      binutils \
      # Required for staticx
      patchelf \
      # Needed for pyinstaller
      zlib-dev

COPY . /buaut
# Smaller better binaries:
# https://github.com/JonathonReinhart/staticx#from-source
RUN pip3 install -r /buaut/requirements.txt && \
    pip3 install scons staticx && \
    pip3 install -e /buaut

# 'Install' upx from image since upx isn't available for aarch64 from Alpine
COPY --from=lansible/upx /usr/bin/upx /usr/bin/upx

# Build bootloader for alpine
# Source: https://github.com/six8/pyinstaller-alpine/blob/develop/python3.7.Dockerfile#L26
RUN git clone --depth 1 --single-branch --branch v4.7 https://github.com/pyinstaller/pyinstaller.git /tmp/pyinstaller \
    && cd /tmp/pyinstaller/bootloader \
    && CFLAGS="-Wno-stringop-overflow -Wno-stringop-truncation" python3 ./waf configure --no-lsb all \
    && pip3 install .. \
    && rm -Rf /tmp/pyinstaller

WORKDIR /buaut
RUN pyinstaller --strip --onefile /usr/bin/buaut


#######################################################################################################################
# Final scratch image
#######################################################################################################################
FROM scratch

# Add description
LABEL org.label-schema.description="BuAut, Bunq Automation for an easier life :)"

# Copy the unprivileged user
COPY --from=builder /etc_passwd /etc/passwd

# Add ssl certificates
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy needed libs(libstdc++.so, libgcc_s.so) for nodejs since it is partially static
# Copy linker to be able to use them (lib/ld-musl)
COPY --from=builder \
    /usr/lib/libstdc++.so.6 \
    /usr/lib/libgcc_s.so.1 \
    /usr/lib/
COPY --from=builder \
    /lib/ld-musl-*.so.1 \
    /lib/libz.so.1 \
    /lib/

# Add compiled binary
COPY --from=builder /buaut/dist/buaut /buaut

USER buaut
ENTRYPOINT ["/buaut"]
CMD ["--help"]
