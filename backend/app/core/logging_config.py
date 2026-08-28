import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger("asistente_jnj")
    if root.handlers:
        return
    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    root.addHandler(handler)
