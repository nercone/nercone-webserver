import os
import uvicorn
from .constants import unix_socket
from nercone_website.databases import MimeTypes

def main():
    MimeTypes.fetch()
    if unix_socket:
        os.umask(0o000)
        uvicorn.run("nercone_website.app:app", uds=unix_socket, workers=4, server_header=False)
    else:
        uvicorn.run("nercone_website.app:app", host="0.0.0.0", port=8080, workers=4, server_header=False)

if __name__ == "__main__":
    main()
