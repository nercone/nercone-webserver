FROM fedora:latest

RUN dnf update -y && dnf install -y git systemd

COPY . /srv/nercone-webserver/
COPY nercone-webserver.service /etc/systemd/system/
COPY nercone-webserver-autoupdater.service /etc/systemd/system/
COPY nercone-webserver-autoupdater.timer /etc/systemd/system/

RUN systemctl enable nercone-webserver.service && systemctl enable nercone-webserver-autoupdater.timer

EXPOSE 80
CMD ["/usr/sbin/init"]
