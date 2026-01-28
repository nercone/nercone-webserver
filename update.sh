sudo /usr/bin/systemctl stop nercone-webserver
/usr/bin/git pull
/home/nercone/.local/bin/uv pip install -r requirements.txt --upgrade
sudo /usr/bin/systemctl start nercone-webserver
