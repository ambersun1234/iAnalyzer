import logging
from typing import Optional


class ColorPalette:
    blue = "\x1b[34;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    purple = "\x1b[35;20m"
    gray = "\x1b[38;20m"
    reset = "\x1b[0m"
    cyan = "\x1b[36;20m"
    dark_gray = "\x1b[90m"


class RequestIdFilter(logging.Filter):
    build_in_fields = [
        "args", "asctime", "created", "exc_text", "exc_info", "filename",
        "funcName", "levelname", "levelno", "lineno", "message", "module",
        "msecs", "msg", "name", "pathname", "process", "process-Name", "processName",
        "relativeCreated", "stack_info", "thread", "thread-Name", "threadName", "taskName"
    ]
    def filter(self, record: logging.LogRecord) -> bool:
        fields = dict()
        for k, v in record.__dict__.items():
            if k not in self.build_in_fields:
                fields[k] = v
        record.fields = fields
        return True


class CustomFormatter(logging.Formatter):
    def extra(self, fields):
        formatted_extra = ""
        for k, v in fields.items():
            formatted_extra += f"{ColorPalette.cyan}{k}={ColorPalette.reset}{v} "
        return formatted_extra

    def format(self, record):
        # Get level color
        level_colors = {
            logging.DEBUG: ColorPalette.blue,
            logging.INFO: ColorPalette.green,
            logging.WARNING: ColorPalette.yellow,
            logging.ERROR: ColorPalette.red,
            logging.CRITICAL: ColorPalette.purple,
        }
        level_color = level_colors.get(record.levelno, ColorPalette.gray)

        # Add padding to level name for visual alignment
        # CRITICAL is the longest at 8 characters, so we pad others to match
        padded_levelname = f"[{record.levelname}]".ljust(10)

        # Format with different colors
        formatted = (
            f"{ColorPalette.dark_gray}{self.formatTime(record)}{ColorPalette.reset} - "
            f"{level_color}{padded_levelname}{ColorPalette.reset} - "
            f"\"{ColorPalette.gray}{record.getMessage()}{ColorPalette.reset}\" "
            f"{self.extra(record.fields)}"
            f"({ColorPalette.gray}{record.name}{ColorPalette.reset}) "
            f"{ColorPalette.yellow}({record.filename}:{record.lineno}){ColorPalette.reset}"
        )

        return formatted


# Create the base logger
logger = logging.getLogger("iAnalyzer")
logger.setLevel(logging.DEBUG)

# Set up the handler
ch = logging.StreamHandler()
ch.setFormatter(CustomFormatter())
ch.setLevel(logging.DEBUG)
ch.addFilter(RequestIdFilter())
logger.addHandler(ch)