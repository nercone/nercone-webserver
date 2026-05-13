import uvicorn
from .config import Files, Directories

def main():
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "filename": str(Files.Logs.uvicorn.relative_to(Directories.base)),
                "formatter": "default"
            },
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default"
            }
        },
        "loggers": {
            "uvicorn": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["file", "console"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["file", "console"], "level": "INFO", "propagate": False}
        }
    }
    uvicorn.run("nercone_website.server:app", host="0.0.0.0", port=8080, workers=4, server_header=False, log_config=log_config)

if __name__ == "__main__":
    main()
