FROM python:3.12-slim

WORKDIR /srv/forage
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Dependencies first (layer caching). Playwright downloads Chromium + system deps.
COPY requirements.txt requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock \
    && playwright install --with-deps chromium \
    && patchright install chromium \
    && scrapling install \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin forage \
    && chmod -R a+rX /ms-playwright

# Application code
COPY app/ app/

# Factory-default config (users override via bind mount in compose)
COPY --chmod=0444 config.example.yaml /etc/forage/config.yaml

ENV FORAGE_CONFIG=/etc/forage/config.yaml \
    HOME=/tmp \
    XDG_CACHE_HOME=/tmp/.cache

EXPOSE 3672

USER 10001:10001

CMD ["python", "-m", "app.main"]
