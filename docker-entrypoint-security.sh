#!/usr/bin/env sh
set -euo pipefail

# Validaciones de entorno para JWT/JWKS sin tocar los entrypoints de Python

if [ "${SKIP_JWT_VALIDATION:-0}" = "1" ]; then
  echo "[security] JWT validation checks skipped (SKIP_JWT_VALIDATION=1)"
else
  : "${JWT_ISSUER:?Falta JWT_ISSUER}"
  : "${JWT_AUDIENCE:?Falta JWT_AUDIENCE}"

  if [ -z "${JWKS_URL:-}" ] && [ -z "${JWKS_PATH:-}" ]; then
    echo "[security] Debe definir JWKS_URL o JWKS_PATH" >&2
    exit 1
  fi

  if [ -n "${JWKS_URL:-}" ]; then
    if command -v wget >/dev/null 2>&1; then
      if ! wget -q --spider "${JWKS_URL}"; then
        echo "[security] No se puede acceder a JWKS_URL=${JWKS_URL}" >&2
        exit 1
      fi
    elif command -v curl >/dev/null 2>&1; then
      if ! curl -fsI "${JWKS_URL}" >/dev/null; then
        echo "[security] No se puede acceder a JWKS_URL=${JWKS_URL}" >&2
        exit 1
      fi
    else
      echo "[security] Ni wget ni curl disponibles para verificar JWKS_URL" >&2
    fi
  fi

  if [ -n "${JWKS_PATH:-}" ] && [ ! -r "${JWKS_PATH}" ]; then
    echo "[security] No se puede leer JWKS_PATH=${JWKS_PATH}" >&2
    exit 1
  fi
fi

exec "$@"