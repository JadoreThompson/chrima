# Monitoring

Port of `chrima-backend/src/chrima/monitoring`. Exposes operational health endpoints.

## Contents

- `controller.MonitoringController` — `GET /monitoring/health` returning `{"status": "ok"}`.

## Interacts with

- `config.SecurityConfig` — permits `/monitoring/**` without authentication.