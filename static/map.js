document.addEventListener("DOMContentLoaded", function () {
    if (!Notification) {
        console.log('could not load notifications');
        return;
    }

    if (Notification.permission !== "granted") {
        Notification.requestPermission();
    }
});


var $selectExclude = $("#exclude-pokemon");
var $selectInclude = $("#include-pokemon");
var $selectNotify = $("#notify-pokemon");

var idToPokemon = {};

$.getJSON("static/locales/pokemon.en.json").done(function(data) {
    var pokeList = []

    $.each(data, function(key, value) {
        pokeList.push( { id: key, text: value } );
        idToPokemon[key] = value;
    });

    // setup the filter lists
    $selectExclude.select2({
        placeholder: "Select Pokémon",
        data: pokeList
    });
    $selectInclude.select2({
        placeholder: "Select Pokémon",
        data: pokeList
    });
    $selectNotify.select2({
        placeholder: "Select Pokémon",
        data: pokeList
    });

    // recall saved lists
    if (localStorage['remember_select_exclude']) {
        $selectExclude.val(JSON.parse(localStorage.remember_select_exclude)).trigger("change");
    }
    if (localStorage['remember_select_include']) {
        $selectInclude.val(JSON.parse(localStorage.remember_select_notify)).trigger("change");
    }
    if (localStorage['remember_select_notify']) {
        $selectNotify.val(JSON.parse(localStorage.remember_select_notify)).trigger("change");
    }
});

var excludedPokemon = [];
var includedPokemon = [];
var notifiedPokemon = [];

$selectExclude.on("change", function (e) {
    excludedPokemon = $selectExclude.val().map(Number);
    clearStaleMarkers();
    localStorage.remember_select_exclude = JSON.stringify(excludedPokemon);
});

$selectInclude.on("change", function (e) {
    includedPokemon = $selectInclude.val().map(Number);
    localStorage.remember_select_include = JSON.stringify(includedPokemon);
});

$selectNotify.on("change", function (e) {
    notifiedPokemon = $selectNotify.val().map(Number);
    localStorage.remember_select_notify = JSON.stringify(notifiedPokemon);
});

var map;
var marker;
var mapPosition;
var mapBounds;

var light2Style=[{"elementType":"geometry","stylers":[{"hue":"#ff4400"},{"saturation":-68},{"lightness":-4},{"gamma":0.72}]},{"featureType":"road","elementType":"labels.icon"},{"featureType":"landscape.man_made","elementType":"geometry","stylers":[{"hue":"#0077ff"},{"gamma":3.1}]},{"featureType":"water","stylers":[{"hue":"#00ccff"},{"gamma":0.44},{"saturation":-33}]},{"featureType":"poi.park","stylers":[{"hue":"#44ff00"},{"saturation":-23}]},{"featureType":"water","elementType":"labels.text.fill","stylers":[{"hue":"#007fff"},{"gamma":0.77},{"saturation":65},{"lightness":99}]},{"featureType":"water","elementType":"labels.text.stroke","stylers":[{"gamma":0.11},{"weight":5.6},{"saturation":99},{"hue":"#0091ff"},{"lightness":-86}]},{"featureType":"transit.line","elementType":"geometry","stylers":[{"lightness":-48},{"hue":"#ff5e00"},{"gamma":1.2},{"saturation":-23}]},{"featureType":"transit","elementType":"labels.text.stroke","stylers":[{"saturation":-64},{"hue":"#ff9100"},{"lightness":16},{"gamma":0.47},{"weight":2.7}]}];
var darkStyle=[{"featureType":"all","elementType":"labels.text.fill","stylers":[{"saturation":36},{"color":"#b39964"},{"lightness":40}]},{"featureType":"all","elementType":"labels.text.stroke","stylers":[{"visibility":"on"},{"color":"#000000"},{"lightness":16}]},{"featureType":"all","elementType":"labels.icon","stylers":[{"visibility":"off"}]},{"featureType":"administrative","elementType":"geometry.fill","stylers":[{"color":"#000000"},{"lightness":20}]},{"featureType":"administrative","elementType":"geometry.stroke","stylers":[{"color":"#000000"},{"lightness":17},{"weight":1.2}]},{"featureType":"landscape","elementType":"geometry","stylers":[{"color":"#000000"},{"lightness":20}]},{"featureType":"poi","elementType":"geometry","stylers":[{"color":"#000000"},{"lightness":21}]},{"featureType":"road.highway","elementType":"geometry.fill","stylers":[{"color":"#000000"},{"lightness":17}]},{"featureType":"road.highway","elementType":"geometry.stroke","stylers":[{"color":"#000000"},{"lightness":29},{"weight":0.2}]},{"featureType":"road.arterial","elementType":"geometry","stylers":[{"color":"#000000"},{"lightness":18}]},{"featureType":"road.local","elementType":"geometry","stylers":[{"color":"#181818"},{"lightness":16}]},{"featureType":"transit","elementType":"geometry","stylers":[{"color":"#000000"},{"lightness":19}]},{"featureType":"water","elementType":"geometry","stylers":[{"lightness":17},{"color":"#525252"}]}];
var pGoStyle=[{"featureType":"landscape.man_made","elementType":"geometry.fill","stylers":[{"color":"#a1f199"}]},{"featureType":"landscape.natural.landcover","elementType":"geometry.fill","stylers":[{"color":"#37bda2"}]},{"featureType":"landscape.natural.terrain","elementType":"geometry.fill","stylers":[{"color":"#37bda2"}]},{"featureType":"poi.attraction","elementType":"geometry.fill","stylers":[{"visibility":"on"}]},{"featureType":"poi.business","elementType":"geometry.fill","stylers":[{"color":"#e4dfd9"}]},{"featureType":"poi.business","elementType":"labels.icon","stylers":[{"visibility":"off"}]},{"featureType":"poi.park","elementType":"geometry.fill","stylers":[{"color":"#37bda2"}]},{"featureType":"road","elementType":"geometry.fill","stylers":[{"color":"#84b09e"}]},{"featureType":"road","elementType":"geometry.stroke","stylers":[{"color":"#fafeb8"},{"weight":"1.25"}]},{"featureType":"road.highway","elementType":"labels.icon","stylers":[{"visibility":"off"}]},{"featureType":"water","elementType":"geometry.fill","stylers":[{"color":"#5ddad6"}]}];

var selectedStyle = 'light';


function handleLocationError(browserHasGeolocation) {
    infoWindow = new google.maps.InfoWindow({map: map});
    infoWindow.setPosition(map.getCenter());
    infoWindow.setContent(browserHasGeolocation ?
                            'Error: The Geolocation service failed.' :
                            'Error: Your browser doesn\'t support geolocation.');
}

function handleBoundsUpdate() {
    mapPosition = map.getCenter()
    mapBounds   = map.getBounds()
}

function initMap() {

    map = new google.maps.Map(document.getElementById('map'), {
        center: {
            lat: center_lat,
            lng: center_lng
        },
        zoom: 16,
        fullscreenControl: true,
        streetViewControl: false,
		mapTypeControl: true,
		mapTypeControlOptions: {
          style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
          position: google.maps.ControlPosition.RIGHT_TOP,
          mapTypeIds: [
              google.maps.MapTypeId.ROADMAP,
              google.maps.MapTypeId.SATELLITE,
              'dark_style',
              'style_light2',
              'style_pgo']
        },
    });

    google.maps.event.addListener(map, "bounds_changed", handleBoundsUpdate);




    marker = new google.maps.Marker({
        position: {
            lat: center_lat,
            lng: center_lng
        },
        map: map,
        animation: google.maps.Animation.DROP
    });

	var style_dark = new google.maps.StyledMapType(darkStyle, {name: "Dark"});
	map.mapTypes.set('dark_style', style_dark);

	var style_light2 = new google.maps.StyledMapType(light2Style, {name: "Light2"});
	map.mapTypes.set('style_light2', style_light2);

	var style_pgo = new google.maps.StyledMapType(pGoStyle, {name: "PokemonGo"});
	map.mapTypes.set('style_pgo', style_pgo);

    map.addListener('maptypeid_changed', function(s) {
        localStorage['map_style'] = this.mapTypeId;
    });

    if (!localStorage['map_style'] || localStorage['map_style'] === 'undefined') {
        localStorage['map_style'] = 'roadmap';
    }

    map.setMapTypeId(localStorage['map_style']);



    // Try HTML5 geolocation.
    if (user_gps==1) {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                var pos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };

                //infoWindow.setPosition(pos);
                //infoWindow.setContent('Location found.');
                map.setCenter(pos);
                marker.setPosition(pos);

                $.ajax({
                    url: "put_user_geo",
                    type: 'GET',
                    data: {
                        'latitude': position.coords.latitude,
                        'longtude': position.coords.longitude
                    },
                    dataType: "json"
                })
            }, function() {
                handleLocationError(true);
            });
        } else {
            // Browser doesn't support Geolocation
            handleLocationError(false);
        }
    }


    initSidebar();
};

function initSidebar() {
    $('#gyms-switch').prop('checked', localStorage.showGyms === 'true');
    $('#pokemon-switch').prop('checked', localStorage.showPokemon === 'true');
    $('#pokestops-switch').prop('checked', localStorage.showPokestops === 'true');
    $('#scanned-switch').prop('checked', localStorage.showScanned === 'true');
    $('#sound-switch').prop('checked', localStorage.playSound === 'true');

    var searchBox = new google.maps.places.SearchBox(document.getElementById('next-location'));

    searchBox.addListener('places_changed', function() {
        var places = searchBox.getPlaces();

        if (places.length == 0) {
            return;
        }

        var loc = places[0].geometry.location;
        $.ajax({
            url: "put_data_geo",
            type: 'GET',
            data: {
                'latitude': loc.lat(),
                'longtude': loc.lng()
            },
            dataType: "json"
        }).done(function(result) {
            $("#next-location").val("");
            var pos = {
                lat: result.latitude,
                lng: result.longitude
            };

            map.setCenter(loc);
            marker.setPosition(loc);
        })
    });
}

var pad = function (number) { return number <= 99 ? ("0" + number).slice(-2) : number; }

function pokemonLabel(name, disappear_time, cd_pokemon, latitude, longitude) {
    disappear_date = new Date(disappear_time)

    var contentstring = `
        <div>
            <b>${name}</b>
            <span> - </span>
            <small>
                <a href='http://www.pokemon.com/us/pokedex/${cd_pokemon}' target='_blank' title='Просматреть статистику'>#${cd_pokemon}</a>
            </small>
        </div>
        <div>
            Исчезнет в ${pad(disappear_date.getHours())}:${pad(disappear_date.getMinutes())}:${pad(disappear_date.getSeconds())}
            <span class='label-countdown' disappears-at='${disappear_time}'>(00m00s)</span></div>
        <div>
            <a href='https://www.google.com/maps/dir/Current+Location/${latitude},${longitude}'
                    target='_blank' title='View in Maps'>Проложить путь</a>
        </div>`;
    return contentstring;
};

function gymLabel(team_id, team_name, gym_id, gym_name, gym_prestige, gym_image, date_change) {
    date_change = new Date(date_change)

    var gym_color = ["0, 0, 0, .4", "74, 138, 202, .6", "240, 68, 58, .6", "254, 217, 40, .6"];
    var gym_logo = gym_types[team_id]
    var str;
    if (team_id == 0) {
        str = `<div><center>
            <div style='padding-bottom: 2px'>${gym_name}</div>
            <div>
                <b style='color:rgba(${gym_color[team_id]})'>${gym_name}</b><br/>
                <b style='color:rgba(${gym_color[team_id]})'>${team_name}</b><br/>
            </div>
            <div>Данные обновлены: ${pad(date_change.getHours())}:${pad(date_change.getMinutes())}:${pad(date_change.getSeconds())}</div>

            </center></div>`;
    } else {
        str = `
<div>
    <center>
        <div style='padding-bottom: 2px'>${gym_name}</div>
        <div>
            <b style='color:rgba(${gym_color[team_id]})'>Команда ${team_name}</b>
            <br/>
            <img height='70px' style='padding: 5px;' src='static/forts/${gym_logo}_large.png'>
        </div>
        <div>Престиж: ${gym_prestige}</div>
        <div>Данные обновлены: ${pad(date_change.getHours())}:${pad(date_change.getMinutes())}:${pad(date_change.getSeconds())}</div>
    </center>
</div>
        `;
    }

    return str;
}

function pokestopLabel(name, image, date_lure_expiration_in, date_change) {
    date_change = new Date(date_change)
    date_lure_expiration = new Date(date_lure_expiration_in)

    var str;

    if (date_lure_expiration_in) {
        str = `
            <div><center>
            <div style='padding-bottom: 2px'>${name}</div>
            <div>Люр истекает: ${pad(date_lure_expiration.getHours())}:${pad(date_lure_expiration.getMinutes())}:${pad(date_lure_expiration.getSeconds())}</div>
            <div>Данные обновлены: ${pad(date_change.getHours())}:${pad(date_change.getMinutes())}:${pad(date_change.getSeconds())}</div>
            </center></div>`;
    } else {
        str = `
            <div><center>
            <div style='padding-bottom: 2px'>${name}</div>
            <div>Данные обновлены: ${pad(date_change.getHours())}:${pad(date_change.getMinutes())}:${pad(date_change.getSeconds())}</div>
            </center></div>`;
    }

    return str;
}

function scannedLabel(scanner_id, last_modified) {
    scanned_date = new Date(last_modified)
    var pad = function (number) { return number <= 99 ? ("0" + number).slice(-2) : number; }

    var contentstring = `
        <div>
            Идентификатор сканера: ${scanner_id}
        </div>
        <div>
            Последние отклик от сканера ${pad(scanned_date.getHours())}:${pad(scanned_date.getMinutes())}:${pad(scanned_date.getSeconds())}
        </div>`;
    return contentstring;
};
// Dicts
// Dicts
map_pokemons = {} // Pokemon
map_gyms = {} // Gyms
map_pokestops = {} // Pokestops
map_scanned = {} // Pokestops

var gym_types = ["Uncontested", "Mystic", "Valor", "Instinct"];
var audio = new Audio('https://github.com/AHAAAAAAA/PokemonGo-Map/raw/develop/static/sounds/ding.mp3');


function setupPokemonMarker(item) {
    //  item.pokemon_name
    //  item.pokemin_id


    var marker = new google.maps.Marker({
        position: {
            lat: item.latitude,
            lng: item.longitude
        },
        map: map,
        icon: 'static/icons/' + item.pokemon_id + '.png'
    });

    marker.infoWindow = new google.maps.InfoWindow({
        content: pokemonLabel(item.pokemon_name, (item.date_disappear-6*60*60*1000), item.pokemon_id, item.latitude, item.longitude)
    });

    if (notifiedPokemon.indexOf(item.pokemon_id) > -1) {
        if(localStorage.playSound === 'true'){
          audio.play();
        }
        sendNotification('Обноаружен покемон ' + item.pokemon_name + '!', 'Жми на карту', 'static/icons/' + item.pokemon_id + '.png')
    }

    addListeners(marker);
    return marker;
};

function setupGymMarker(item) {
    //  item.team_id
    //  item.team_name
    //  item.gym_id
    //  item.gym_name
    //  item.gym_prestige

    var marker = new google.maps.Marker({
        position: {
            lat: item.latitude,
            lng: item.longitude
        },
        map: map,
        icon: 'static/forts/' + gym_types[item.team_id] + '.png'
    });

    marker.infoWindow = new google.maps.InfoWindow({

        content: gymLabel(item.team_id, item.team_name, item.gym_id, item.gym_name, item.gym_prestige, item.gym_image,  (item.date_change-6*60*60*1000))
    });

    addListeners(marker);
    return marker;
};

function setupPokestopMarker(item) {
    var imagename = item.date_lure_expiration ? "PstopLured" : "Pstop";
    var marker = new google.maps.Marker({
        position: {
            lat: item.latitude,
            lng: item.longitude
        },
        map: map,
        icon: 'static/forts/' + imagename + '.png',
    });

    marker.infoWindow = new google.maps.InfoWindow({
        content: pokestopLabel(item.name, item.image, (item.date_lure_expiration-6*60*60*1000), (item.date_change-6*60*60*1000))
    });

    addListeners(marker);
    return marker;
};

function getColorByDate(value){
    //Changes the Color from Red to green over 15 mins
    var diff = (Date.now() - value) / 1000 / 60 / 15;

    if(diff > 1){
        diff = 1;
    }

    //value from 0 to 1 - Green to Red
    var hue=((1-diff)*120).toString(10);
    return ["hsl(",hue,",100%,50%)"].join("");
}

function setupScannedMarker(item) {
    var circleCenter = new google.maps.LatLng(item.latitude, item.longitude);

    var marker = new google.maps.Circle({
        map: map,
        center: circleCenter,
        radius: item.distance,    // 10 miles in metres
        fillColor: getColorByDate((item.date_change-6*60*60*1000)),
        strokeWeight: 1
    });

    marker.infoWindow = new google.maps.InfoWindow({
         content: scannedLabel(item.id, (item.date_change-6*60*60*1000)),
         position: circleCenter
     });

    addListeners(marker);
    return marker;
};

function addListeners(marker) {
    marker.addListener('click', function() {
        marker.infoWindow.open(map, marker);
        updateLabelDiffTime();
        marker.persist = true;
    });

    google.maps.event.addListener(marker.infoWindow, 'closeclick', function() {
        marker.persist = null;
    });

    marker.addListener('mouseover', function() {
        marker.infoWindow.open(map, marker);
        updateLabelDiffTime();
    });

    marker.addListener('mouseout', function() {
        if (!marker.persist) {
            marker.infoWindow.close();
        }
    });
    return marker
};

function clearStaleMarkers() {
    $.each(map_pokemons, function(key, value) {

        if ((map_pokemons[key]['date_disappear']-6*60*60*1000) < new Date().getTime() ||
                excludedPokemon.indexOf(map_pokemons[key]['pokemon_id']) >= 0 || (includedPokemon.length > 0 && includedPokemon.indexOf(map_pokemons[key]['pokemon_id']) == -1) ) {
            map_pokemons[key].marker.setMap(null);
            delete map_pokemons[key];
        }
    });

    $.each(map_scanned, function(key, value) {
        //If older than 15mins remove
        if ((map_scanned[key]['date_change']-6*60*60*1000) < (new Date().getTime() - 15 * 60 * 1000)) {
            map_scanned[key].marker.setMap(null);
            delete map_scanned[key];
        }
    });
};

function updateMap() {
    if (map) {
        localStorage.showPokemon = localStorage.showPokemon || true;
        localStorage.showGyms = localStorage.showGyms || true;
        localStorage.showPokestops = localStorage.showPokestops || false;
        localStorage.showScanned = localStorage.showScanned || false;

        $.ajax({
            url: "get_data",
            type: 'GET',
            data: {
                'pokemon': localStorage.showPokemon,
                'pokestops': localStorage.showPokestops,
                'gyms': localStorage.showGyms,
                'scanned': localStorage.showScanned,
                'latitude': mapPosition.lat(),
                'longitude': mapPosition.lng(),
                'ne_latitude': mapBounds.getNorthEast().lat(),
                'ne_longitude': mapBounds.getNorthEast().lng(),
                'sw_latitude': mapBounds.getSouthWest().lat(),
                'sw_longitude': mapBounds.getSouthWest().lng(),
                'pokemon_time': pokemon_time,
                'pokemon_ids': pokemon_ids
            },
            dataType: "json"
        }).done(function(result) {
          $.each(result.pokemons, function(i, item){
              if (!localStorage.showPokemon) {
                  return false; // in case the checkbox was unchecked in the meantime.
              }
              if (!(item.encounter_id in map_pokemons) &&
                        excludedPokemon.indexOf(item.pokemon_id) < 0) {
                  // add marker to map and item to dict
                  if (item.marker) item.marker.setMap(null);
                  item.marker = setupPokemonMarker(item);
                  map_pokemons[item.encounter_id] = item;
              }
            });

            $.each(result.pokestops, function(i, item) {
                if (!localStorage.showPokestops) {
                    return false;
                } else if (!(item.id in map_pokestops)) { // add marker to map and item to dict
                    // add marker to map and item to dict
                    if (item.marker) item.marker.setMap(null);
                    item.marker = setupPokestopMarker(item);
                    map_pokestops[item.id] = item;
                }

            });

            $.each(result.gyms, function(i, item){
                if (!localStorage.showGyms) {
                    return false; // in case the checkbox was unchecked in the meantime.
                }

                if (item.gym_id in map_gyms) {
                    // if team has changed, create new marker (new icon)
                    if (map_gyms[item.gym_id].team_id != item.team_id) {
                        map_gyms[item.gym_id].marker.setMap(null);
                        map_gyms[item.gym_id].marker = setupGymMarker(item);
                    } else { // if it hasn't changed generate new label only (in case prestige has changed)
                        map_gyms[item.gym_id].marker.infoWindow = new google.maps.InfoWindow({
                            content: gymLabel(item.team_id, item.team_name, item.gym_id, item.gym_name, item.gym_prestige, item.gym_image,  (item.date_change-6*60*60*1000))
                        });
                    }
                }
                else { // add marker to map and item to dict
                    if (item.marker) item.marker.setMap(null);
                    item.marker = setupGymMarker(item);
                    map_gyms[item.gym_id] = item;
                }

            });

            $.each(result.scanned, function(i, item) {
                if (!localStorage.showScanned) {
                    return false;
                }

                if (item.id in map_scanned) {
                    map_scanned[item.id].marker.setOptions({fillColor: getColorByDate(item.date_change-6*60*60*1000)});
                }
                else { // add marker to map and item to dict
                    if (item.marker) item.marker.setMap(null);
                    item.marker = setupScannedMarker(item);
                    map_scanned[item.id] = item;
                }

            });

            if (pokemon_time == -1) {
                clearStaleMarkers();
            }
        });
    };
};

window.setInterval(updateMap, 5000);
updateMap();

document.getElementById('gyms-switch').onclick = function() {
    localStorage["showGyms"] = this.checked;
    if (this.checked) {
        updateMap();
    } else {
        $.each(map_gyms, function(key, value) {
            map_gyms[key].marker.setMap(null);
        });
        map_gyms = {}
    }
};

$('#pokemon-switch').change(function() {
    localStorage["showPokemon"] = this.checked;
    if (this.checked) {
        updateMap();
    } else {
        $.each(map_pokemons, function(key, value) {
            map_pokemons[key].marker.setMap(null);
        });
        map_pokemons = {}
    }
});

$('#pokestops-switch').change(function() {
    localStorage["showPokestops"] = this.checked;
    if (this.checked) {
        updateMap();
    } else {
        $.each(map_pokestops, function(key, value) {
            map_pokestops[key].marker.setMap(null);
        });
        map_pokestops = {}
    }
});

$('#sound-switch').change(function() {
    localStorage["playSound"] = this.checked;
});

$('#scanned-switch').change(function() {
    localStorage["showScanned"] = this.checked;
    if (this.checked) {
        updateMap();
    } else {
        $.each(map_scanned, function(key, value) {
            map_scanned[key].marker.setMap(null);
        });
        map_scanned = {}
    }
});

var updateLabelDiffTime = function() {
    $('.label-countdown').each(function(index, element) {
        var disappearsAt = new Date(parseInt(element.getAttribute("disappears-at")));
        var now = new Date();

        var difference = Math.abs(disappearsAt - now);
        var hours = Math.floor(difference / 36e5);
        var minutes = Math.floor((difference - (hours * 36e5)) / 6e4);
        var seconds = Math.floor((difference - (hours * 36e5) - (minutes * 6e4)) / 1e3);

        if (disappearsAt < now) {
            timestring = "(expired)";
        } else {
            timestring = "(";
            if (hours > 0)
                timestring = hours + "h";

            timestring += ("0" + minutes).slice(-2) + "m";
            timestring += ("0" + seconds).slice(-2) + "s";
            timestring += ")";
        }

        $(element).text(timestring)
    });
};

window.setInterval(updateLabelDiffTime, 1000);

function sendNotification(title, text, icon) {
    if (Notification.permission !== "granted") {
        Notification.requestPermission();
    } else {
        var notification = new Notification(title, {
            icon: icon,
            body: text,
            sound: 'sounds/ding.mp3'
        });

        notification.onclick = function () {
            window.open(window.location.href);
        };
    }
}