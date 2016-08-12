#!/usr/bin/env bash

worker_path="/home/apache/org-tatarnikov-pokestats/";

cd "${worker_path}/.python";
git pull;

cat /dev/null > "${worker_path}/.log/access_log";
cat /dev/null > "${worker_path}/.log/error_log";

killall -9 httpd;
systemctl restart httpd;
