SELECT
	p.id as pokemon_id,
    p.name as pokemon_name,
	count(ps.cd_pokemon) as respawn_count
FROM
	db_pokestats.pokemon_spawnpoint ps,
    db_pokestats.pokemon p
WHERE
	ps.cd_pokemon = p.id
GROUP BY
	p.name, p.id
ORDER BY
	p.id
;


SELECT
	p.id as pokemon_id,
    p.name as pokemon_name,
	count(ps.cd_pokemon) as respawn_count,
    min((ps.date_disappear - now())) as respawn_seconds
FROM
	db_pokestats.pokemon_spawnpoint ps,
    db_pokestats.pokemon p
WHERE
		ps.cd_pokemon = p.id
    and ps.date_disappear > now()
    and ps.cd_pokemon in (2,3,4,5,6,8,9,12,15,23,24,25,26,28,30,31,33,34,36,37,38,40,45,47,49,51,53,55,56,57,58,59,61,62,63,64,65,66,67,68,71,73,75,76,78,79,80,82,83,84,85,87,89,91,93,94,95,99,100,102,103,105,106,106,107,108,110,112,113,114,115,117,121,122,123,125,127,128,130,131,132,134,135,136,138,139,140,141,144,145)
GROUP BY
	p.name, p.id
ORDER BY
	p.id
;