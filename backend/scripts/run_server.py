import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

import uvicorn  # noqa: E402

from config.settings import settings  # noqa: E402

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
    )

