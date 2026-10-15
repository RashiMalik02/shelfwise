# ---- build stage: resolve and install Python deps into a self-contained venv ----
FROM python:3.13-slim AS build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
 && pip install -r /tmp/requirements.txt \
 && pip uninstall -y pip


# ---- runtime stage: no compilers, no pip cache, no root ----
FROM python:3.13-slim AS runtime

LABEL org.opencontainers.image.title="shelfwise-backend" \
      org.opencontainers.image.description="Shelfwise inventory API (FastAPI)"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# pip is not needed at runtime, and the copy shipped in the base image vendors old
# urllib3/msgpack/setuptools that Trivy flags as HIGH. Removing it shrinks the attack surface.
RUN python -m pip uninstall -y pip \
 && rm -rf /usr/local/lib/python3.13/ensurepip \
 && groupadd --system --gid 10001 shelfwise \
 && useradd --system --uid 10001 --gid shelfwise --no-create-home --shell /usr/sbin/nologin shelfwise

WORKDIR /app
COPY --from=build /opt/venv /opt/venv
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY --chmod=755 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
