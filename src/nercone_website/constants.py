import subprocess
from pathlib import Path

class Directories:
    base = Path.cwd()
    public = base.joinpath("public")
    logs = base.joinpath("logs")
    databases = base.joinpath("databases")

class Files:
    access_counter = Directories.databases.joinpath("access_counter.txt")

    class Logs:
        app = Directories.logs.joinpath("app.log")
        access = Directories.logs.joinpath("access.log")
        error = Directories.logs.joinpath("error.log")

class Repositories:
    class Server:
        url = subprocess.run(["/usr/bin/git", "remote", "get-url", "origin"], text=True, capture_output=True, cwd=Directories.base).stdout.strip()
        version = subprocess.run(["/usr/bin/git", "rev-parse", "--short", "HEAD"], text=True, capture_output=True, cwd=Directories.base).stdout.strip()

    class Contents:
        url = subprocess.run(["/usr/bin/git", "remote", "get-url", "origin"], text=True, capture_output=True, cwd=Directories.public).stdout.strip()
        version = subprocess.run(["/usr/bin/git", "rev-parse", "--short", "HEAD"], text=True, capture_output=True, cwd=Directories.public).stdout.strip()

class Hostnames:
    local = ["localhost", "127.0.0.1"]
    public = ["nercone.dev", "nerc1.dev", "diamondgotcat.net", "d-g-c.net"]
    onion = ["nerconexssicpt442ngh5lt7hwyh47sk3rob3iei263s7lcjann633id.onion", "4sbb7xhdn4meuesnqvcreewk6sjnvchrsx4lpnxmnjhz2soat74finid.onion"]
    all = local + public + onion
