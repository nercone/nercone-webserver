import os
import uvicorn
from nercone_website.databases import MimeTypes

def main():
    MimeTypes.fetch()
    if "WEBSITE_UDS" in os.environ:
        os.umask(0o000)
        uvicorn.run("nercone_website.app:app", uds=os.environ.get("WEBSITE_UDS"), workers=4, server_header=False)
    else:
        uvicorn.run("nercone_website.app:app", host="0.0.0.0", port=8080, workers=4, server_header=False)

if __name__ == "__main__":
    main()
