''' Helper functions for dataset schedules
'''
import logging

import boto3
from tzlocal import get_localzone_name

from cid.utils import exec_env

logger = logging.getLogger(__name__)

MAPPING_REGION_2_TIMEZONE = {
    "us-east-1": "America/New_York",
    "us-east-2": "America/New_York",
    "us-west-1": "America/Los_Angeles",
    "us-west-2": "America/Los_Angeles",
    "af-south-1": "Africa/Blantyre",
    "ap-east-1": "Asia/Hong_Kong",
    "ap-south-1": "Asia/Kolkata",
    "ap-southeast-3": "Asia/Jakarta",
    "ap-southeast-4": "Australia/Melbourne",
    "ap-northeast-3": "Asia/Tokyo",
    "ap-northeast-2": "Asia/Seoul",
    "ap-southeast-1": "Asia/Singapore",
    "ap-southeast-2": "Australia/Sydney",
    "ap-northeast-1": "Asia/Tokyo",
    "ca-central-1": "America/Toronto",
    "eu-central-1": "Europe/Berlin",
    "eu-west-1": "Europe/Dublin",
    "eu-west-2": "Europe/London",
    "eu-south-1": "Europe/Rome",
    "eu-west-3": "Europe/Paris",
    "eu-south-2": "Europe/Madrid",
    "eu-north-1": "Europe/Stockholm",
    "eu-central-2": "Europe/Zurich",
    "me-south-1": "Asia/Riyadh",
    "me-central-1": "Asia/Dubai",
    "sa-east-1": "America/Sao_Paulo",
    "us-gov-east-1": "US/Eastern",
    "us-gov-west-1": "US/Pacific",
}

# Can be replaced with pytz.all_timezones
ALL_TIMEZONES = '''
    ACT
    AET
    AGT
    ART
    AST
    Africa/Abidjan
    Africa/Accra
    Africa/Addis_Ababa
    Africa/Algiers
    Africa/Asmara
    Africa/Asmera
    Africa/Bamako
    Africa/Bangui
    Africa/Banjul
    Africa/Bissau
    Africa/Blantyre
    Africa/Brazzaville
    Africa/Bujumbura
    Africa/Cairo
    Africa/Casablanca
    Africa/Ceuta
    Africa/Conakry
    Africa/Dakar
    Africa/Dar_es_Salaam
    Africa/Djibouti
    Africa/Douala
    Africa/El_Aaiun
    Africa/Freetown
    Africa/Gaborone
    Africa/Harare
    Africa/Johannesburg
    Africa/Juba
    Africa/Kampala
    Africa/Khartoum
    Africa/Kigali
    Africa/Kinshasa
    Africa/Lagos
    Africa/Libreville
    Africa/Lome
    Africa/Luanda
    Africa/Lubumbashi
    Africa/Lusaka
    Africa/Malabo
    Africa/Maputo
    Africa/Maseru
    Africa/Mbabane
    Africa/Mogadishu
    Africa/Monrovia
    Africa/Nairobi
    Africa/Ndjamena
    Africa/Niamey
    Africa/Nouakchott
    Africa/Ouagadougou
    Africa/Porto-Novo
    Africa/Sao_Tome
    Africa/Timbuktu
    Africa/Tripoli
    Africa/Tunis
    Africa/Windhoek
    America/Adak
    America/Anchorage
    America/Anguilla
    America/Antigua
    America/Araguaina
    America/Argentina/Buenos_Aires
    America/Argentina/Catamarca
    America/Argentina/ComodRivadavia
    America/Argentina/Cordoba
    America/Argentina/Jujuy
    America/Argentina/La_Rioja
    America/Argentina/Mendoza
    America/Argentina/Rio_Gallegos
    America/Argentina/Salta
    America/Argentina/San_Juan
    America/Argentina/San_Luis
    America/Argentina/Tucuman
    America/Argentina/Ushuaia
    America/Aruba
    America/Asuncion
    America/Atikokan
    America/Atka
    America/Bahia
    America/Bahia_Banderas
    America/Barbados
    America/Belem
    America/Belize
    America/Blanc-Sablon
    America/Boa_Vista
    America/Bogota
    America/Boise
    America/Buenos_Aires
    America/Cambridge_Bay
    America/Campo_Grande
    America/Cancun
    America/Caracas
    America/Catamarca
    America/Cayenne
    America/Cayman
    America/Chicago
    America/Chihuahua
    America/Coral_Harbour
    America/Cordoba
    America/Costa_Rica
    America/Creston
    America/Cuiaba
    America/Curacao
    America/Danmarkshavn
    America/Dawson
    America/Dawson_Creek
    America/Denver
    America/Detroit
    America/Dominica
    America/Edmonton
    America/Eirunepe
    America/El_Salvador
    America/Ensenada
    America/Fort_Wayne
    America/Fortaleza
    America/Glace_Bay
    America/Godthab
    America/Goose_Bay
    America/Grand_Turk
    America/Grenada
    America/Guadeloupe
    America/Guatemala
    America/Guayaquil
    America/Guyana
    America/Halifax
    America/Havana
    America/Hermosillo
    America/Indiana/Indianapolis
    America/Indiana/Knox
    America/Indiana/Marengo
    America/Indiana/Petersburg
    America/Indiana/Tell_City
    America/Indiana/Vevay
    America/Indiana/Vincennes
    America/Indiana/Winamac
    America/Indianapolis
    America/Inuvik
    America/Iqaluit
    America/Jamaica
    America/Jujuy
    America/Juneau
    America/Kentucky/Louisville
    America/Kentucky/Monticello
    America/Knox_IN
    America/Kralendijk
    America/La_Paz
    America/Lima
    America/Los_Angeles
    America/Louisville
    America/Lower_Princes
    America/Maceio
    America/Managua
    America/Manaus
    America/Marigot
    America/Martinique
    America/Matamoros
    America/Mazatlan
    America/Mendoza
    America/Menominee
    America/Merida
    America/Metlakatla
    America/Mexico_City
    America/Miquelon
    America/Moncton
    America/Monterrey
    America/Montevideo
    America/Montreal
    America/Montserrat
    America/Nassau
    America/New_York
    America/Nipigon
    America/Nome
    America/Noronha
    America/North_Dakota/Beulah
    America/North_Dakota/Center
    America/North_Dakota/New_Salem
    America/Ojinaga
    America/Panama
    America/Pangnirtung
    America/Paramaribo
    America/Phoenix
    America/Port-au-Prince
    America/Port_of_Spain
    America/Porto_Acre
    America/Porto_Velho
    America/Puerto_Rico
    America/Rainy_River
    America/Rankin_Inlet
    America/Recife
    America/Regina
    America/Resolute
    America/Rio_Branco
    America/Rosario
    America/Santa_Isabel
    America/Santarem
    America/Santiago
    America/Santo_Domingo
    America/Sao_Paulo
    America/Scoresbysund
    America/Shiprock
    America/Sitka
    America/St_Barthelemy
    America/St_Johns
    America/St_Kitts
    America/St_Lucia
    America/St_Thomas
    America/St_Vincent
    America/Swift_Current
    America/Tegucigalpa
    America/Thule
    America/Thunder_Bay
    America/Tijuana
    America/Toronto
    America/Tortola
    America/Vancouver
    America/Virgin
    America/Whitehorse
    America/Winnipeg
    America/Yakutat
    America/Yellowknife
    Antarctica/Casey
    Antarctica/Davis
    Antarctica/DumontDUrville
    Antarctica/Macquarie
    Antarctica/Mawson
    Antarctica/McMurdo
    Antarctica/Palmer
    Antarctica/Rothera
    Antarctica/South_Pole
    Antarctica/Syowa
    Antarctica/Troll
    Antarctica/Vostok
    Arctic/Longyearbyen
    Asia/Aden
    Asia/Almaty
    Asia/Amman
    Asia/Anadyr
    Asia/Aqtau
    Asia/Aqtobe
    Asia/Ashgabat
    Asia/Ashkhabad
    Asia/Baghdad
    Asia/Bahrain
    Asia/Baku
    Asia/Bangkok
    Asia/Beirut
    Asia/Bishkek
    Asia/Brunei
    Asia/Calcutta
    Asia/Chita
    Asia/Choibalsan
    Asia/Chongqing
    Asia/Chungking
    Asia/Colombo
    Asia/Dacca
    Asia/Damascus
    Asia/Dhaka
    Asia/Dili
    Asia/Dubai
    Asia/Dushanbe
    Asia/Gaza
    Asia/Harbin
    Asia/Hebron
    Asia/Ho_Chi_Minh
    Asia/Hong_Kong
    Asia/Hovd
    Asia/Irkutsk
    Asia/Istanbul
    Asia/Jakarta
    Asia/Jayapura
    Asia/Jerusalem
    Asia/Kabul
    Asia/Kamchatka
    Asia/Karachi
    Asia/Kashgar
    Asia/Kathmandu
    Asia/Katmandu
    Asia/Khandyga
    Asia/Kolkata
    Asia/Krasnoyarsk
    Asia/Kuala_Lumpur
    Asia/Kuching
    Asia/Kuwait
    Asia/Macao
    Asia/Macau
    Asia/Magadan
    Asia/Makassar
    Asia/Manila
    Asia/Muscat
    Asia/Nicosia
    Asia/Novokuznetsk
    Asia/Novosibirsk
    Asia/Omsk
    Asia/Oral
    Asia/Phnom_Penh
    Asia/Pontianak
    Asia/Pyongyang
    Asia/Qatar
    Asia/Qyzylorda
    Asia/Rangoon
    Asia/Riyadh
    Asia/Riyadh87
    Asia/Riyadh88
    Asia/Riyadh89
    Asia/Saigon
    Asia/Sakhalin
    Asia/Samarkand
    Asia/Seoul
    Asia/Shanghai
    Asia/Singapore
    Asia/Srednekolymsk
    Asia/Taipei
    Asia/Tashkent
    Asia/Tbilisi
    Asia/Tehran
    Asia/Tel_Aviv
    Asia/Thimbu
    Asia/Thimphu
    Asia/Tokyo
    Asia/Ujung_Pandang
    Asia/Ulaanbaatar
    Asia/Ulan_Bator
    Asia/Urumqi
    Asia/Ust-Nera
    Asia/Vientiane
    Asia/Vladivostok
    Asia/Yakutsk
    Asia/Yekaterinburg
    Asia/Yerevan
    Atlantic/Azores
    Atlantic/Bermuda
    Atlantic/Canary
    Atlantic/Cape_Verde
    Atlantic/Faeroe
    Atlantic/Faroe
    Atlantic/Jan_Mayen
    Atlantic/Madeira
    Atlantic/Reykjavik
    Atlantic/South_Georgia
    Atlantic/St_Helena
    Atlantic/Stanley
    Australia/ACT
    Australia/Adelaide
    Australia/Brisbane
    Australia/Broken_Hill
    Australia/Canberra
    Australia/Currie
    Australia/Darwin
    Australia/Eucla
    Australia/Hobart
    Australia/LHI
    Australia/Lindeman
    Australia/Lord_Howe
    Australia/Melbourne
    Australia/NSW
    Australia/North
    Australia/Perth
    Australia/Queensland
    Australia/South
    Australia/Sydney
    Australia/Tasmania
    Australia/Victoria
    Australia/West
    Australia/Yancowinna
    BET
    BST
    Brazil/Acre
    Brazil/DeNoronha
    Brazil/East
    Brazil/West
    CAT
    CET
    CNT
    CST
    CST6CDT
    CTT
    Canada/Atlantic
    Canada/Central
    Canada/East-Saskatchewan
    Canada/Eastern
    Canada/Mountain
    Canada/Newfoundland
    Canada/Pacific
    Canada/Saskatchewan
    Canada/Yukon
    Chile/Continental
    Chile/EasterIsland
    Cuba
    EAT
    ECT
    EET
    EST
    EST5EDT
    Egypt
    Eire
    Etc/GMT
    Etc/GMT+0
    Etc/GMT+1
    Etc/GMT+10
    Etc/GMT+11
    Etc/GMT+12
    Etc/GMT+2
    Etc/GMT+3
    Etc/GMT+4
    Etc/GMT+5
    Etc/GMT+6
    Etc/GMT+7
    Etc/GMT+8
    Etc/GMT+9
    Etc/GMT-0
    Etc/GMT-1
    Etc/GMT-10
    Etc/GMT-11
    Etc/GMT-12
    Etc/GMT-13
    Etc/GMT-14
    Etc/GMT-2
    Etc/GMT-3
    Etc/GMT-4
    Etc/GMT-5
    Etc/GMT-6
    Etc/GMT-7
    Etc/GMT-8
    Etc/GMT-9
    Etc/GMT0
    Etc/Greenwich
    Etc/UCT
    Etc/UTC
    Etc/Universal
    Etc/Zulu
    Europe/Amsterdam
    Europe/Andorra
    Europe/Athens
    Europe/Belfast
    Europe/Belgrade
    Europe/Berlin
    Europe/Bratislava
    Europe/Brussels
    Europe/Bucharest
    Europe/Budapest
    Europe/Busingen
    Europe/Chisinau
    Europe/Copenhagen
    Europe/Dublin
    Europe/Gibraltar
    Europe/Guernsey
    Europe/Helsinki
    Europe/Isle_of_Man
    Europe/Istanbul
    Europe/Jersey
    Europe/Kaliningrad
    Europe/Kiev
    Europe/Lisbon
    Europe/Ljubljana
    Europe/London
    Europe/Luxembourg
    Europe/Madrid
    Europe/Malta
    Europe/Mariehamn
    Europe/Minsk
    Europe/Monaco
    Europe/Moscow
    Europe/Nicosia
    Europe/Oslo
    Europe/Paris
    Europe/Podgorica
    Europe/Prague
    Europe/Riga
    Europe/Rome
    Europe/Samara
    Europe/San_Marino
    Europe/Sarajevo
    Europe/Simferopol
    Europe/Skopje
    Europe/Sofia
    Europe/Stockholm
    Europe/Tallinn
    Europe/Tirane
    Europe/Tiraspol
    Europe/Uzhgorod
    Europe/Vaduz
    Europe/Vatican
    Europe/Vienna
    Europe/Vilnius
    Europe/Volgograd
    Europe/Warsaw
    Europe/Zagreb
    Europe/Zaporozhye
    Europe/Zurich
    GB
    GB-Eire
    GMT
    GMT0
    Greenwich
    HST
    Hongkong
    IET
    IST
    Iceland
    Indian/Antananarivo
    Indian/Chagos
    Indian/Christmas
    Indian/Cocos
    Indian/Comoro
    Indian/Kerguelen
    Indian/Mahe
    Indian/Maldives
    Indian/Mauritius
    Indian/Mayotte
    Indian/Reunion
    Iran
    Israel
    JST
    Jamaica
    Japan
    Kwajalein
    Libya
    MET
    MIT
    MST
    MST7MDT
    Mexico/BajaNorte
    Mexico/BajaSur
    Mexico/General
    Mideast/Riyadh87
    Mideast/Riyadh88
    Mideast/Riyadh89
    NET
    NST
    NZ
    NZ-CHAT
    Navajo
    PLT
    PNT
    PRC
    PRT
    PST
    PST8PDT
    Pacific/Apia
    Pacific/Auckland
    Pacific/Bougainville
    Pacific/Chatham
    Pacific/Chuuk
    Pacific/Easter
    Pacific/Efate
    Pacific/Enderbury
    Pacific/Fakaofo
    Pacific/Fiji
    Pacific/Funafuti
    Pacific/Galapagos
    Pacific/Gambier
    Pacific/Guadalcanal
    Pacific/Guam
    Pacific/Honolulu
    Pacific/Johnston
    Pacific/Kiritimati
    Pacific/Kosrae
    Pacific/Kwajalein
    Pacific/Majuro
    Pacific/Marquesas
    Pacific/Midway
    Pacific/Nauru
    Pacific/Niue
    Pacific/Norfolk
    Pacific/Noumea
    Pacific/Pago_Pago
    Pacific/Palau
    Pacific/Pitcairn
    Pacific/Pohnpei
    Pacific/Ponape
    Pacific/Port_Moresby
    Pacific/Rarotonga
    Pacific/Saipan
    Pacific/Samoa
    Pacific/Tahiti
    Pacific/Tarawa
    Pacific/Tongatapu
    Pacific/Truk
    Pacific/Wake
    Pacific/Wallis
    Pacific/Yap
    Poland
    Portugal
    ROK
    SST
    Singapore
    SystemV/AST4
    SystemV/AST4ADT
    SystemV/CST6
    SystemV/CST6CDT
    SystemV/EST5
    SystemV/EST5EDT
    SystemV/HST10
    SystemV/MST7
    SystemV/MST7MDT
    SystemV/PST8
    SystemV/PST8PDT
    SystemV/YST9
    SystemV/YST9YDT
    Turkey
    UCT
    US/Alaska
    US/Aleutian
    US/Arizona
    US/Central
    US/East-Indiana
    US/Eastern
    US/Hawaii
    US/Indiana-Starke
    US/Michigan
    US/Mountain
    US/Pacific
    US/Pacific-New
    US/Samoa
    UTC
    Universal
    VST
    W-SU
    WET
    Zulu
'''.strip()


def get_timezone_from_aws_region(region):
    """ Get Timezone from AWS region. """
    if region not in MAPPING_REGION_2_TIMEZONE:
        logger.warning(f'Unkown region {region}. please create a github issue to add it.')
    return MAPPING_REGION_2_TIMEZONE.get(region, "America/New_York")


def get_default_timezone():
    """ Get timzone best guess from Shell or from Region. """

    # In a case of running lambda of chloudshell the local timezone does not make much sense
    # so we take the one from the region
    if exec_env()['terminal'] in ('cloudshell', 'lambda'):
        region = boto3.session.Session().region_name
        return get_timezone_from_aws_region(region)

    # for all other cases use local timezone of the shell
    return get_localzone_name()


def get_all_timezones():
    """Get all zones"""
    return sorted(ALL_TIMEZONES)
