import os
import logging
from strands import Agent
from strands.telemetry import StrandsTelemetry

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
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4318"
StrandsTelemetry().setup_otlp_exporter()

CONSIGLIERE_AGENT_PROMPT = """
TODO
"""

consigliere = Agent()

if __name__ == "__main__":
    print(
        "Ask a question in any subject area, and I'll route it to the appropriate specialist."
    )
    print("Type 'exit' to quit.")

    while True:
        try:
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                print("\nGoodbye! 👋")
                break

            response = consigliere(
                user_input,
            )

            # Extract and print only the relevant content from the specialized agent's response
            content = str(response)
            print(content)

        except KeyboardInterrupt:
            print("\n\nExecution interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try asking a different question.")
