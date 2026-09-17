FROM alpine:3.22.1@sha256:4562b419adf48c5f3c763995d6014c123b3ce1d2e0ef2613b189779caa787192
COPY cache /inputs
RUN cd /inputs && sha256sum -c SHA256SUMS && apk add --no-network /inputs/*.apk
COPY scripts /recipe/scripts
COPY build /recipe/build
COPY licenses /recipe/licenses
COPY docs /recipe/docs
COPY README.md /recipe/README.md
ENV LANG=C LC_ALL=C TZ=UTC SOURCE_DATE_EPOCH=1781913600
WORKDIR /recipe
ENTRYPOINT ["bash", "/recipe/scripts/build.sh"]
