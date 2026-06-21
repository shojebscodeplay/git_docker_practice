import logging
import sys


def configure_logging() -> None:
    """
    Configure application-wide logging.

    Production note: inside a container, log to stdout/stderr only.
    Docker / the orchestrator captures that stream and ships it to
    CloudWatch / Loki / ELK etc. Writing to a local file inside the
    container is a trap — that file dies the moment the container
    restarts or gets rescheduled.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # uvicorn.access is noisy at INFO — nginx already logs every request,
    # no need to double-log it on the app side.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
