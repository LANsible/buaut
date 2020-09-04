ARG ARCHITECTURE
#######################################################################################################################
# Package binary with Pyinstaller
#######################################################################################################################
# Using non alpine for glibc which pyinstaller needs
FROM multiarch/debian-debootstrap:${ARCHITECTURE}-bullseye as builder

# Add unprivileged user
RUN echo "buaut:x:1000:1000:buaut:/:" > /etc_passwd

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

# Set musl as default
ENV CC=/usr/bin/musl-gcc

COPY . /buaut
RUN pip3 install -r /buaut/requirements.txt && \
    pip3 install pyinstaller scons && \
    pip3 install -e /buaut && \
    pip3 install https://github.com/JonathonReinhart/staticx/archive/master.zip

WORKDIR /buaut
# Adds libnss and libresolv to binary since these are used for DNS resolving by Python
RUN pyinstaller --strip --onefile /usr/local/bin/buaut && \
    staticx \
        --strip \
        -l /lib/x86_64-linux-gnu/libnss_dns.so.2 \
        -l /lib/x86_64-linux-gnu/libresolv.so.2 \
        dist/buaut dist/buaut_static && \
    chmod +x dist/buaut_static

#######################################################################################################################
# Final scratch image
#######################################################################################################################
FROM scratch
ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8

# Add description
LABEL org.label-schema.description="BuAut, Bunq Automation for an easier life :)"

# TODO: Look why this breaks:
# "Failed to open /proc/self/exe: Permission denied"
# Copy the unprivileged user
# COPY --from=builder /etc_passwd /etc/passwd
COPY --from=builder /etc/passwd /etc/passwd

# Add locale otherwise Click does not work:
# https://click.palletsprojects.com/en/7.x/python3/
COPY --from=builder /usr/lib/locale/C.UTF-8 /usr/lib/locale/C.UTF-8

# Add ssl certificates
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Add compiled binary
COPY --from=builder /buaut/dist/buaut_static /buaut

# TODO: enable when user is available again
# USER buaut
ENTRYPOINT ["/buaut"]
CMD ["--help"]