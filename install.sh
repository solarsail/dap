#!/bin/bash
yum install -y epel-release
yum install -y python-pip uwsgi uwsgi-plugin-python mariadb-devel gcc python-devel redis nginx
python setup.py install
systemctl enable sdap
