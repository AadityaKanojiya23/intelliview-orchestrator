# Monitoring and System Health

## Overview

Intelliview Orchestrator provides monitoring for system health,
API performance, worker health, queue depth, and service availability.

## Status Page

The monitoring dashboard provides a simple system health view.

It displays:

- Overall system health
- Service health status
- Current monitoring information
- Last checked time

The dashboard is available through the monitoring dashboard setup.

## Alerts

Prometheus alert rules are configured in:

`monitoring/alerts/alert_rules.yml`

The following conditions are monitored:

- High API error rate
- High API response time
- Unhealthy workers
- High queue depth
- Redis health
- PostgreSQL health

Alerts use warning and critical severity levels.

## Local Monitoring

1. Start the application and monitoring services.
2. Start Prometheus using the project's Docker/monitoring setup.
3. Open the monitoring dashboard.
4. Check the overall system health.
5. Check Prometheus to verify that metrics are being collected.
6. Check the alert status when a monitored component becomes unhealthy.

## Health Status

The status page uses the following states:

- **Healthy** – system is operating normally.
- **Degraded** – a monitored component requires attention.
- **Critical** – a critical service or dependency is unhealthy.

## Troubleshooting

If monitoring is not working:

1. Check that Prometheus is running.
2. Check that the monitored services are reachable.
3. Verify the Prometheus configuration.
4. Check `monitoring/alerts/alert_rules.yml`.
5. Check application and monitoring logs.