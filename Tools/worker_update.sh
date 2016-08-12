#!/usr/bin/env bash

worker_id=$1;

if [ -z "$1" ]; then
    worker_id=1;
fi;

worker_path="/home/apache/org-tatarnikov-pokestats/";
worker_date=$(date +"%Y-%m-%d-%H-%M-%S");
worker_pid="$(cat ${worker_path}/.run/worker.${worker_id}.pid)";
worker_log_main="${worker_path}/.log/worker.${worker_id}.log";
worker_log_nohup="${worker_path}/.log/worker.${worker_id}.nohup.out";

worker_log_cloud="/mnt/cloud/_owncloud/data/v.tatarnikov/files/Projects/_pokestats/_log";
worker_log_cloud_main="${worker_log_cloud}/${worker_date}.worker.${worker_id}.log";
worker_log_cloud_nohup="${worker_log_cloud}/${worker_date}.nohup.${worker_id}.log";

if [ -f "/proc/${worker_pid}/comm" ]; then
    if [ "$(cat /proc/${worker_pid}/comm)" -eq "Worker.py" ]; then
        kill ${worker_pid} > /dev/null 2> /dev/null;
        sleep 2
        kill -9 ${worker_pid} > /dev/null 2> /dev/null;
        sleep 2
    fi;
fi;

if [ ! -d "${worker_log_cloud}" ]; then
    #  Если на сервере нет Owncloud'a то просто оставляем логи тут
    worker_log_cloud_main="${worker_path}/.log/${worker_date}.worker.${worker_id}.log";
    worker_log_cloud_nohup="${worker_path}/.log/${worker_date}.nohup.${worker_id}.log";
fi;

cat ${worker_log_main}  > "$worker_log/$worker_date.worker.$worker_id.log";
cat ${worker_log_nohup} > "$worker_log/$worker_date.nohup.$worker_id.log";

if [ -d "${worker_log_cloud}" ]; then
    chown -R apache:apache "${worker_log_cloud}";
    sudo -u apache php /home/apache/org-tatarnikov-owncloud/occ files:scan  v.tatarnikov --path /v.tatarnikov/files/Projects/_pokestats > /dev/null;
fi;

rm -f "${worker_log_main}" "${worker_log_nohup}";

cd "${worker_path}/.python";
git pull;

nohup "${worker_path}/.python/Worker.py" -s ${worker_id} > "${worker_log_nohup}" &

sleep 2

worker_pid="$(cat ${worker_path}/.run/worker.${worker_id}.pid)";

renice -7 ${worker_pid};

