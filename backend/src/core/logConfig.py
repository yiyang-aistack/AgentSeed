import os
import time
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# colorlog is an optional dependency: if missing, silently fall back to the standard
# Formatter rather than crashing the whole module import.
# It is up to your favoriate formatting.
try:
    import colorlog

    _HAS_COLORLOG = True
except ImportError:
    _HAS_COLORLOG = False

# ============================================================
# Project root = the repository root, i.e. the parent of backend/
# backend/src/core/logConfig.py -> core -> src -> backend -> <repo root>
# ============================================================
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"


def resolve_log_dir():
    """Resolve the log storage directory.

    Prefer reading the LOG_DIR environment variable (from .env, e.g. `./logs`).
    - Relative paths are resolved against the project root (consistent with Tomcat's logs dir
      semantics).
    - Falls back to <project root>/logs when not configured / empty.
    """
    env_dir = os.getenv("LOG_DIR")
    if env_dir:
        p = Path(env_dir).expanduser()
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        p = p.resolve()
    else:
        p = DEFAULT_LOG_DIR.resolve()
    os.makedirs(p, exist_ok=True)
    return str(p)


class AgentSeedRotatingFileHandler(TimedRotatingFileHandler):
    """A daily-rolling log FileHandler modeled after Tomcat catalina.

    Behavior:
        - Live logs are always written to  <log_dir>/agentseed.log
        - After a day boundary, the previous day is rolled into  <log_dir>/agentseed.log.yyyymmdd
          e.g. agentseed.log.20260409 (history files get a YYYYMMDD suffix appended)

    Differences from the standard TimedRotatingFileHandler:
        - The directory / main filename / rolling suffix are all fixed by this class,
          so uvicorn dictConfig can reference it directly as `"class"` with no extra args.
        - rotation_filename is overridden to ensure the history filename is strictly
          `agentseed.log.YYYYMMDD`, avoiding extension concatenation differences across Python
          versions.
    """

    # Date suffix for history files (separated from the main filename by a ".",
    # i.e. agentseed.log.20260409)
    _ROLLOVER_DATE_SUFFIX = "%Y%m%d"

    def __init__(self, backup_count: int = 0, encoding: str = "utf-8"):
        # backup_count: number of history files to keep. 0 means do not auto-delete, keep them all.
        log_dir = resolve_log_dir()
        self.backup_count = backup_count
        base_filename = os.path.join(log_dir, "agentseed.log")

        # Must manually set interval to 1 and when to midnight to roll at 0:00 daily.
        super().__init__(
            base_filename,
            when="midnight",
            interval=1,
            backupCount=backup_count,
            encoding=encoding,
            delay=True,
            utc=False,
        )
        # Override the default date suffix to YYYYMMDD and rebuild the matching regex.
        self.suffix = self._ROLLOVER_DATE_SUFFIX
        # extMatch is used to identify history filenames during rollover / backupCount cleanup.
        import re

        self.extMatch = re.compile(r"^\.\d{8}$")

    def rotation_filename(self, default_name: str) -> str:
        """Pin the history filename to `baseFilename + '.' + YYYYMMDD`.

        default_name is already composed by the parent class, but different interpreter
        versions may append an extra extension (e.g. ".log.") to the original suffix.
        Here we simply return the result determined by the format string, guaranteeing
        it is always agentseed.log.<YYYYMMDD>.
        """
        date_suffix = time.strftime(self._ROLLOVER_DATE_SUFFIX, time.localtime())
        return self.baseFilename + "." + date_suffix

    def getFilesToDelete(self):
        """When backupCount > 0, only retire history files matching `agentseed.log.YYYYMMDD`."""
        if self.backupCount <= 0:
            return []
        log_dir = os.path.dirname(self.baseFilename)
        prefix = os.path.basename(self.baseFilename) + "."
        dir_name, base_name = os.path.split(self.baseFilename)
        file_names = os.listdir(log_dir)
        result = []
        for file_name in file_names:
            if file_name.startswith(prefix):
                suffix = file_name[len(prefix) :]
                if self.extMatch.match("." + suffix):
                    match = True
                else:
                    # Compatible case where the standard library may add an extra
                    # separator to the suffix.
                    match = False
                if match:
                    result.append(os.path.join(dir_name, file_name))
        result.sort()
        # Only remove the oldest files that exceed the retention count.
        return result[: max(0, len(result) - self.backupCount)]

    def doRollover(self):
        """Trigger daily rollover: agentseed.log -> agentseed.log.YYYYMMDD, then rebuild the
        current log."""
        if self.stream:
            self.stream.close()
            self.stream = None

        dfs = self.getFilesToDelete()
        for df in dfs:
            try:
                os.remove(df)
            except OSError:
                pass

        new_fn = self.rotation_filename(None)
        if os.path.exists(new_fn):
            # If the target already exists, remove the old backup first to ensure a clean append.
            try:
                os.remove(new_fn)
            except OSError:
                pass
        # Atomic rename: different sources (e.g. reload restart) on the same day
        # will not overwrite the same-named file.
        try:
            self.rotate(self.baseFilename, new_fn)
        except OSError:
            # If the file is in use (a handle opened in append mode), simply write to the new file.
            pass

        # Recompute the next rollover time.
        current_time = int(time.time())
        new_rollover_at = self.computeRollover(current_time)
        while new_rollover_at <= current_time:
            new_rollover_at = new_rollover_at + self.interval
        self.rolloverAt = new_rollover_at


def get_uvicorn_log_config(level=None, enable_color=True, backup_count=None, to_console=True):
    """Return a logging dictConfig for uvicorn.

    Compared to the native implementation, this adds:
        - a `file` handler: rolls daily like Tomcat catalina writing to logs/agentseed.log
          (history files agentseed.log.YYYYMMDD).
        - keeps the console handler (can be disabled via to_console=False, writing to file only).

    Arguments:
        level:        log level (defaults to LOG_LEVEL from .env)
        enable_color: whether to enable color on the console (keeps original semantics)
        backup_count: number of history logs to keep, defaults to LOG_BACKUP_COUNT from .env,
            0 = no cleanup
        to_console:   whether to also output to the console (default True => console + file)
    """
    log_level = level or os.getenv("LOG_LEVEL", "INFO").upper()
    if backup_count is None:
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", "0") or "0")

    # Only truly enable color on the console when colorlog is available, otherwise fall back
    # to plain format.
    console_color = enable_color and _HAS_COLORLOG

    colored_fmt = "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    plain_fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # NOTE on logging.dictConfig schema:
    # - Standard-library formatters must NOT carry a custom "()" key: dictConfig
    #   then instantiates logging.Formatter natively, mapping "format" -> fmt.
    #   Passing "()": logging.Formatter + "format" goes through configure_custom,
    #   which forwards the key literally -> TypeError (Formatter takes `fmt`,
    #   not `format`).
    # - Custom classes (colorlog.ColoredFormatter) DO need "()"; its constructor
    #   parameter is also `fmt`, not `format`.
    formatters: dict[str, dict] = {}

    if to_console:
        if console_color:
            # Custom colored formatter -- dictConfig calls configure_custom,
            # so the key must match the constructor parameter name (`fmt`).
            formatters["console"] = {
                "()": colorlog.ColoredFormatter,
                "fmt": colored_fmt,
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "log_colors": {  # colorlog supported colors
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bg_white",
                },
            }
        else:
            # Plain stdlib formatter --  no "()", dictConfig maps "format" -> fmt.
            formatters["console"] = {
                "format": plain_fmt,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }

    # File: no color, easier for grep / editor reading
    formatters["file"] = {
        "format": plain_fmt,
        "datefmt": "%Y-%m-%d %H:%M:%S",
    }

    handlers = {}
    root_handlers = []

    if to_console:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "console",
        }
        root_handlers.append("console")

    handlers["file"] = {
        # Reference this project's custom daily-rolling handler by the string "class"
        # (backup_count is passed through the constructor argument).
        "class": "src.core.logConfig.AgentSeedRotatingFileHandler",
        "backup_count": backup_count,
        "formatter": "file",
    }
    root_handlers.append("file")

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        # The root logger uses the console and file handlers selected above.
        "root": {
            "level": log_level,
            "handlers": root_handlers,
        },
        # Explicitly configure watchfiles' log levels to avoid spam from DEBUG logs.
        "loggers": {
            "watchfiles": {
                "level": "WARNING",
                "handlers": [],
                "propagate": False,
            },
            "watchfiles.main": {
                "level": "WARNING",
                "handlers": [],
                "propagate": False,
            },
        },
    }
