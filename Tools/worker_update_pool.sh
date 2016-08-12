#!/usr/bin/env bash
worker_mode="$1";
worker_path="/home/apache/org-tatarnikov-pokestats/";
worker_pool="/home/apache/org-tatarnikov-pokestats/.etc/worker_pool";

worker_index_first=2;
worker_index_last=13;

if [ -z "$1" ]; then
    worker_mode="check";
fi;

if [ -f "${worker_pool}" ]; then
    . "${worker_pool}";
fi;

for worker_id in $(seq ${worker_index_first} ${worker_index_last}); do
    if [ -f "${worker_path}/.run/worker.${worker_id}.pid)" ]; then
        worker_pid="$(cat ${worker_path}/.run/worker.${worker_id}.pid)";

        if [ "z$worker_mode" -eq "zupdate" ]; then
            if [ -f "/proc/${worker_pid}/comm" ]; then
                if [ "$(cat /proc/${worker_pid}/comm)" -eq "Worker.py" ]; then
                    kill ${worker_pid} > /dev/null 2> /dev/null;
                    sleep 2
                    kill -9 ${worker_pid} > /dev/null 2> /dev/null;
                    sleep 2
                fi;
            fi;
        fi;

        if [ ! -f "/proc/${worker_pid}/comm" ]; then
            "${worker_path}/.python/Tools/worker_update.sh" ${worker_id};
        fi;
    else
        "${worker_path}/.python/Tools/worker_update.sh" ${worker_id};
    fi;
done;

