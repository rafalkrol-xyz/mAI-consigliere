import os
import logging

from strands.telemetry import StrandsTelemetry
from agents.consigliere import run_app

# When LOG_LEVEL is unset (that's the default behavior, no logs are written
log_level = os.getenv("LOG_LEVEL")
logger = logging.getLogger(__name__)

logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()],
    level=log_level,
)

# Running OTeL collector locally using:
# https://opentelemetry.io/docs/collector/quick-start/
# ```bash
# docker run \
#   -p 127.0.0.1:4317:4317 \
#   -p 127.0.0.1:4318:4318 \
#   -p 127.0.0.1:55679:55679 \
#   otel/opentelemetry-collector:0.144.0 \
#   2>&1
# ```
#
# Set the OTEL_EXPORTER_OTLP_ENDPOINT environment variable when starting the app to setup OTeL,
# ```bash
# OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 uv run main.py
# ```
# TODO: create a dotenv file for all the env vars

if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
    logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set, skipping OTLP setup")
else:
    logger.info("Setting up OTLP exporter")
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4318"
    StrandsTelemetry().setup_otlp_exporter()

if __name__ == "__main__":
    run_app()
