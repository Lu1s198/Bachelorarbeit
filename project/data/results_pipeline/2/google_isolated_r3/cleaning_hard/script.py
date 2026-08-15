import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r3/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    'de': 'DE', 'deutschland': 'DE', 'germany': 'DE', 'deu': 'DE', 'ger': 'DE', 'brd': 'DE',
    'at': 'AT', 'österreich': 'AT', 'oesterreich': 'AT', 'austria': 'AT', 'aut': 'AT',
    'ch': 'CH', 'schweiz': 'CH', 'switzerland': 'CH', 'che': 'CH', 'sui': 'CH',
    'us': 'US', 'usa': 'US', 'united states': 'US', 'united states of america': 'US', 'vereinigte staaten': 'US', 'usofa': 'US',
    'gb': 'GB', 'uk': 'GB', 'united kingdom': 'GB', 'großbritannien': 'GB', 'grossbritannien': 'GB', 'great britain': 'GB', 'gbr': 'GB', 'england': 'GB',
    'fr': 'FR', 'frankreich': 'FR', 'france': 'FR', 'fra': 'FR',
    'it': 'IT', 'italien': 'IT', 'italy': 'IT', 'ita': 'IT',
    'es': 'ES', 'spanien': 'ES', 'spain': 'ES', 'esp': 'ES',
    'nl': 'NL', 'niederlande': 'NL', 'netherlands': 'NL', 'nld': 'NL', 'holland': 'NL',
    'be': 'BE', 'belgien': 'BE', 'belgium': 'BE', 'bel': 'BE',
    'pl': 'PL', 'polen': 'PL', 'poland': 'PL', 'pol': 'PL',
    'cz': 'CZ', 'tschechien': 'CZ', 'czech republic': 'CZ', 'czechia': 'CZ', 'cze': 'CZ',
    'dk': 'DK', 'dänemark': 'DK', 'daenemark': 'DK', 'denmark': 'DK', 'dnk': 'DK',
    'se': 'SE', 'schweden': 'SE', 'sweden': 'SE', 'swe': 'SE',
    'no': 'NO', 'norwegen': 'NO', 'norway': 'NO', 'nor': 'NO',
    'fi': 'FI', 'finnland': 'FI', 'finland': 'FI', 'fin': 'FI',
    'pt': 'PT', 'portugal': 'PT', 'prt': 'PT',
    'gr': 'GR', 'griechenland': 'GR', 'greece': 'GR', 'grc': 'GR',
    'ie': 'IE', 'irland': 'IE', 'ireland': 'IE', 'irl': 'IE',
    'lu': 'LU', 'luxemburg': 'LU', 'luxembourg': 'LU', 'lux': 'LU',
    'hu': 'HU', 'ungarn': 'HU', 'hungary': 'HU', 'hun': 'HU',
    'ro': 'RO', 'rumänien': 'RO', 'rumaenien': 'RO', 'romania': 'RO', 'rou': 'RO', 'rom': 'RO',
    'bg': 'BG', 'bulgarien': 'BG', 'bulgaria': 'BG', 'bgr': 'BG',
    'hr': 'HR', 'kroatien': 'HR', 'croatia': 'HR', 'hrv': 'HR',
    'si': 'SI', 'slowenien': 'SI', 'slovenia': 'SI', 'svn': 'SI',
    'sk': 'SK', 'slowakei': 'SK', 'slovakia': 'SK', 'svk': 'SK',
    'jp': 'JP', 'japan': 'JP', 'jpn': 'JP',
    'cn': 'CN', 'china': 'CN', 'chn': 'CN',
    'in': 'IN', 'indien': 'IN', 'india': 'IN', 'ind': 'IN',
    'br': 'BR', 'brasilien': 'BR', 'brazil': 'BR', 'bra': 'BR',
    'ca': 'CA', 'kanada': 'CA', 'canada': 'CA', 'can': 'CA',
    'au': 'AU', 'australien': 'AU', 'australia': 'AU', 'aus': 'AU',
    'mx': 'MX', 'mexiko': 'MX', 'mexico': 'MX', 'mex': 'MX',
    'ru': 'RU', 'russland': 'RU', 'russia': 'RU', 'rus': 'RU',
    'tr': 'TR', 'türkei': 'TR', 'tuerkei': 'TR', 'turkey': 'TR', 'tur': 'TR',
    'za': 'ZA', 'südafrika': 'ZA', 'suedafrika': 'ZA', 'south africa': 'ZA', 'zaf': 'ZA',
    'ua': 'UA', 'ukraine': 'UA', 'ukr': 'UA',
    'ee': 'EE', 'estland': 'EE', 'estonia': 'EE', 'est': 'EE',
    'lv': 'LV', 'lettland': 'LV', 'latvia': 'LV', 'lva': 'LV',
    'lt': 'LT', 'litauen': 'LT', 'lithuania': 'LT', 'ltu': 'LT',
}

valid_alpha2 = {
    'AD', 'AE', 'AF', 'AG', 'AI', 'AL', 'AM', 'AO', 'AQ', 'AR', 'AS', 'AT', 'AU', 'AW', 'AX', 'AZ',
    'BA', 'BB', 'BD', 'BE', 'BF', 'BG', 'BH', 'BI', 'BJ', 'BL', 'BM', 'BN', 'BO', 'BQ', 'BR', 'BS',
    'BT', 'BV', 'BW', 'BY', 'BZ', 'CA', 'CC', 'CD', 'CF', 'CG', 'CH', 'CI', 'CK', 'CL', 'CM', 'CN',
    'CO', 'CR', 'CU', 'CV', 'CW', 'CX', 'CY', 'CZ', 'DE', 'DJ', 'DK', 'DM', 'DO', 'DZ', 'EC', 'EE',
    'EG', 'EH', 'ER', 'ES', 'ET', 'FI', 'FJ', 'FK', 'FM', 'FO', 'FR', 'GA', 'GB', 'GD', 'GE', 'GF',
    'GG', 'GH', 'GI', 'GL', 'GM', 'GN', 'GP', 'GQ', 'GR', 'GS', 'GT', 'GU', 'GW', 'GY', 'HK', 'HM',
    'HN', 'HR', 'HT', 'HU', 'ID', 'IE', 'IL', 'IM', 'IN', 'IO', 'IQ', 'IR', 'IS', 'IT', 'JE', 'JM',
    'JO', 'JP', 'KE', 'KG', 'KH', 'KI', 'KM', 'KN', 'KP', 'KR', 'KW', 'KY', 'KZ', 'LA', 'LB', 'LC',
    'LI', 'LK', 'LR', 'LS', 'LT', 'LU', 'LV', 'LY', 'MA', 'MC', 'MD', 'ME', 'MF', 'MG', 'MH', 'MK',
    'ML', 'MM', 'MN', 'MO', 'MP', 'MQ', 'MR', 'MS', 'MT', 'MU', 'MV', 'MW', 'MX', 'MY', 'MZ', 'NA',
    'NC', 'NE', 'NF', 'NG', 'NI', 'NL', 'NO', 'NP', 'NR', 'NU', 'NZ', 'OM', 'PA', 'PE', 'PF', 'PG',
    'PH', 'PK', 'PL', 'PM', 'PN', 'PR', 'PS', 'PT', 'PW', 'PY', 'QA', 'RE', 'RO', 'RS', 'RU', 'RW',
    'SA', 'SB', 'SC', 'SD', 'SE', 'SG', 'SH', 'SI', 'SJ', 'SK', 'SL', 'SM', 'SN', 'SO', 'SR', 'SS',
    'ST', 'SV', 'SX', 'SY', 'SZ', 'TC', 'TD', 'TF', 'TG', 'TH', 'TJ', 'TK', 'TL', 'TM', 'TN', 'TO',
    'TR', 'TT', 'TV', 'TW', 'TZ', 'UA', 'UG', 'UM', 'US', 'UY', 'UZ', 'VA', 'VC', 'VE', 'VG', 'VI',
    'VN', 'VU', 'WF', 'WS', 'YE', 'YT', 'ZA', 'ZM', 'ZW'
}

def clean_country(val):
    if pd.isna(val):
        return 'UNKNOWN'
    s = str(val).strip()
    if not s:
        return 'UNKNOWN'
    s_upper = s.upper()
    if s_upper in valid_alpha2:
        return s_upper
    s_lower = s.lower()
    if s_lower in country_map:
        return country_map[s_lower]
    return 'UNKNOWN'

df['country'] = df['country'].apply(clean_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)