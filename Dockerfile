#######################################################################################################################
# Package binary with Pyinstaller
#######################################################################################################################
FROM alpine:3.17 as builder

# Add unprivileged user
RUN echo "buaut:x:1000:1000:buaut:/:" > /etc_passwd

RUN apk add --no-cache \
      python3-dev \
      py3-pip \
      build-base \
      # Needed for pbr version since not released to pypi
      git \
      # Needed for pyinstaller
      binutils

COPY . /buaut
RUN pip3 install -r /buaut/requirements.txt && \
    pip3 install pyinstaller && \
    pip3 install -e /buaut

# 'Install' upx from image since upx isn't available for aarch64 from Alpine
# used by the --strip command of pyinstaller
COPY --from=lansible/upx /usr/bin/upx /usr/bin/upx

# using staticx executable will result in an error:
# buaut: Failed to open /proc/self/exe: Permission denied
# There is some magic involved so decided against it
# https://github.com/pyinstaller/pyinstaller/blob/f8d589f427fb409157f15ad7c0dd3fc4e46ff93c/bootloader/src/pyi_path.c#L298
# https://github.com/JonathonReinhart/staticx/pull/8
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

# Add ssl certificates for SSL connections to Bunq
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy needed libs(libstdc++.so, libgcc_s.so) for for buaut since it just partitally static
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
COPY --from=builder /buaut/dist/buaut /usr/bin/buaut

USER buaut
ENTRYPOINT ["/usr/bin/buaut"]
CMD ["--help"]
