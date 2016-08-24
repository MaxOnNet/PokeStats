#!/usr/bin/env bash
path="/mnt/cloud/_owncloud/data/v.tatarnikov/files/Projects/_pokestats/_backup";
db_user="srv_pokestats"
db_password="3aNC7nVcPPpa2q"
db_name="db_pokestats"
db_host="127.0.0.1"

path_backup="${path}/${db_name}-`date +%Y-%m-%d-%H-%M`.sql";
path_backup_current="${path}/${db_name}-current.sql";

path_web="/home/apache/org-tatarnikov-pokestats/database"
path_web_structure="${path_web}/current.stricture.sql";
path_web_dump_pokemon="${path_web}/current.dump.pokemon.sql";
path_web_dump_scanners="${path_web}/current.dump.scanners.sql";
path_web_dump_pokestop="${path_web}/current.dump.pokestop.sql";
path_web_dump_gym="${path_web}/current.dump.gym.sql";

mkdir -p "${path}";
mkdir -p "${path_web}";

mysqldump   --host=${db_host} \
            --user=${db_user} \
            --password=${db_password} \
            --no-create-db \
            --no-create-info \
            --extended-insert \
            --complete-insert \
            ${db_name} > ${path_backup};

mysqldump   --host=${db_host} \
            --user=${db_user} \
            --password=${db_password} \
            --no-data \
            ${db_name} > ${path_web_structure};

mysqldump   --host=${db_host} \
            --user=${db_user} \
            --password=${db_password} \
            --no-create-db \
            --no-create-info \
            --extended-insert \
            --complete-insert \
            ${db_name} \
            --ignore-table=${db_name}.scanner \
            --ignore-table=${db_name}.scanner_account \
            --ignore-table=${db_name}.scanner_account_statistic \
            --ignore-table=${db_name}.scanner_location \
            --ignore-table=${db_name}.scanner_proxy \
            --ignore-table=${db_name}.scanner_server \
            --ignore-table=${db_name}.scanner_statistic \
            --ignore-table=${db_name}.scanner_mode > ${path_web_dump_pokemon};

mysqldump   --host=${db_host} \
            --user=${db_user} \
            --password=${db_password} \
            --no-create-db \
            --no-create-info \
            --extended-insert \
            --complete-insert \
            ${db_name} \
            --ignore-table=${db_name}.gym \
            --ignore-table=${db_name}.gym_membership \
            --ignore-table=${db_name}.trainer \
            --ignore-table=${db_name}.team \
            --ignore-table=${db_name}.pokemon \
            --ignore-table=${db_name}.pokemon_spawnpoint \
            --ignore-table=${db_name}.pokestop \
            --ignore-table=${db_name}.scanner \
            --ignore-table=${db_name}.scanner_account \
            --ignore-table=${db_name}.scanner_account_statistic \
            --ignore-table=${db_name}.scanner_location \
            --ignore-table=${db_name}.scanner_proxy \
            --ignore-table=${db_name}.scanner_server \
            --ignore-table=${db_name}.scanner_statistic > ${path_web_dump_scanners};

mysqldump   --host=${db_host} \
            --user=${db_user} \
            --password=${db_password} \
            --no-create-db \
            --extended-insert \
            --complete-insert \
            ${db_name} \
            --ignore-table=${db_name}.gym \
            --ignore-table=${db_name}.gym_membership \
            --ignore-table=${db_name}.trainer \
            --ignore-table=${db_name}.team \
            --ignore-table=${db_name}.pokemon \
            --ignore-table=${db_name}.pokemon_spawnpoint \
            --ignore-table=${db_name}.scanner \
            --ignore-table=${db_name}.scanner_account \
            --ignore-table=${db_name}.scanner_account_statistic \
            --ignore-table=${db_name}.scanner_location \
            --ignore-table=${db_name}.scanner_proxy \
            --ignore-table=${db_name}.scanner_server \
            --ignore-table=${db_name}.scanner_statistic \
            --ignore-table=${db_name}.scanner_mode > ${path_web_dump_pokestop};

mysqldump   --host=${db_host} \
            --user=${db_user} \
            --password=${db_password} \
            --no-create-db \
            --extended-insert \
            --complete-insert \
            ${db_name} \
            --ignore-table=${db_name}.pokestop \
            --ignore-table=${db_name}.gym_membership \
            --ignore-table=${db_name}.trainer \
            --ignore-table=${db_name}.team \
            --ignore-table=${db_name}.pokemon \
            --ignore-table=${db_name}.pokemon_spawnpoint \
            --ignore-table=${db_name}.scanner \
            --ignore-table=${db_name}.scanner_account \
            --ignore-table=${db_name}.scanner_account_statistic \
            --ignore-table=${db_name}.scanner_location \
            --ignore-table=${db_name}.scanner_proxy \
            --ignore-table=${db_name}.scanner_server \
            --ignore-table=${db_name}.scanner_statistic \
            --ignore-table=${db_name}.scanner_mode > ${path_web_dump_gym};





#echo "Чистим логины и пароли"
echo " Компрессируем данные";
rm -f ${path_web_structure}.gz ${path_web_dump_pokemon}.gz ${path_web_dump_scanners}.gz ${path_web_dump_gym}.gz ${path_web_dump_pokestop}.gz;

cat ${path_backup} > ${path_backup_current};
cd ${path_web};
gzip -9 ${path_backup} --stdout > ${path_backup}.gz;

gzip -9 ${path_web_structure} --stdout > ${path_web_structure}.gz;
gzip -9 ${path_web_dump_pokemon} --stdout > ${path_web_dump_pokemon}.gz;
gzip -9 ${path_web_dump_scanners} --stdout > ${path_web_dump_scanners}.gz;
gzip -9 ${path_web_dump_gym} --stdout > ${path_web_dump_gym}.gz;
gzip -9 ${path_web_dump_pokestop} --stdout > ${path_web_dump_pokestop}.gz;

rm -rf ${db_backup};

date +%Y-%m-%d-%H-%M > ${path_web}/last_update.txt

chown -R apache:apache ${path};
chown -R apache:apache ${path_web};

echo "Загружаем данные в OwnCloud";
sudo -u apache php /home/apache/org-tatarnikov-owncloud/occ files:scan  v.tatarnikov --path /v.tatarnikov/files/Projects/_pokestats > /dev/null;