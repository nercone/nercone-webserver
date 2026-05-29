import uvicorn
from nercone_website.databases import MimeTypes

def main():
    MimeTypes.fetch()
    uvicorn.run("nercone_website.app:app", host="0.0.0.0", port=8080, workers=4, server_header=False)

if __name__ == "__main__":
    main()
