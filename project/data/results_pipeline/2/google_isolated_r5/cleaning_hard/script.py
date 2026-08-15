import os
import pandas as pd

input_path = r'C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/_reference/cleaning_medium/output.parquet'
output_path = r'C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_isolated_r5/cleaning_hard/output.parquet'

df = pd.read_parquet(input_path)

country_map = {
    # DE
    'de': 'DE', 'deu': 'DE', 'ger': 'DE', 'germany': 'DE', 'deutschland': 'DE', 'dtl': 'DE', 'deutsch': 'DE', 'brd': 'DE',
    # US
    'us': 'US', 'usa': 'US', 'united states': 'US', 'united states of america': 'US', 'vereinigte staaten': 'US', 'vereinigte staaten von amerika': 'US', 'amerika': 'US', 'america': 'US',
    # GB
    'gb': 'GB', 'gbr': 'GB', 'uk': 'GB', 'united kingdom': 'GB', 'great britain': 'GB', 'großbritannien': 'GB', 'grossbritannien': 'GB', 'england': 'GB',
    # AT
    'at': 'AT', 'aut': 'AT', 'austria': 'AT', 'österreich': 'AT', 'oesterreich': 'AT',
    # CH
    'ch': 'CH', 'che': 'CH', 'switzerland': 'CH', 'schweiz': 'CH', 'suisse': 'CH', 'svizzera': 'CH',
    # FR
    'fr': 'FR', 'fra': 'FR', 'france': 'FR', 'frankreich': 'FR',
    # IT
    'it': 'IT', 'ita': 'IT', 'italy': 'IT', 'italien': 'IT',
    # ES
    'es': 'ES', 'esp': 'ES', 'spain': 'ES', 'spanien': 'ES',
    # NL
    'nl': 'NL', 'nld': 'NL', 'netherlands': 'NL', 'niederlande': 'NL', 'holland': 'NL',
    # BE
    'be': 'BE', 'bel': 'BE', 'belgium': 'BE', 'belgien': 'BE',
    # PL
    'pl': 'PL', 'pol': 'PL', 'poland': 'PL', 'polen': 'PL',
    # CA
    'ca': 'CA', 'can': 'CA', 'canada': 'CA', 'kanada': 'CA',
    # AU
    'au': 'AU', 'aus': 'AU', 'australia': 'AU', 'australien': 'AU',
    # CN
    'cn': 'CN', 'chn': 'CN', 'china': 'CN',
    # JP
    'jp': 'JP', 'jpn': 'JP', 'japan': 'JP',
    # BR
    'br': 'BR', 'bra': 'BR', 'brazil': 'BR', 'brasilien': 'BR',
    # IN
    'in': 'IN', 'ind': 'IN', 'india': 'IN', 'indien': 'IN',
    # RU
    'ru': 'RU', 'rus': 'RU', 'russia': 'RU', 'russland': 'RU',
    # SE
    'se': 'SE', 'swe': 'SE', 'sweden': 'SE', 'schweden': 'SE',
    # NO
    'no': 'NO', 'nor': 'NO', 'norway': 'NO', 'norwegen': 'NO',
    # DK
    'dk': 'DK', 'dnk': 'DK', 'denmark': 'DK', 'dänemark': 'DK', 'daenemark': 'DK',
    # FI
    'fi': 'FI', 'fin': 'FI', 'finland': 'FI', 'finnland': 'FI',
    # PT
    'pt': 'PT', 'prt': 'PT', 'portugal': 'PT',
    # GR
    'gr': 'GR', 'grc': 'GR', 'greece': 'GR', 'griechenland': 'GR',
    # TR
    'tr': 'TR', 'tur': 'TR', 'turkey': 'TR', 'türkei': 'TR', 'tuerkei': 'TR',
    # MX
    'mx': 'MX', 'mex': 'MX', 'mexico': 'MX', 'mexiko': 'MX',
    # AR
    'ar': 'AR', 'arg': 'AR', 'argentina': 'AR', 'argentinien': 'AR',
    # ZA
    'za': 'ZA', 'zaf': 'ZA', 'south africa': 'ZA', 'südafrika': 'ZA', 'suedafrika': 'ZA',
    # EG
    'eg': 'EG', 'egy': 'EG', 'egypt': 'EG', 'ägypten': 'EG', 'aegypten': 'EG',
    # IE
    'ie': 'IE', 'irl': 'IE', 'ireland': 'IE', 'irland': 'IE',
    # CZ
    'cz': 'CZ', 'cze': 'CZ', 'czech republic': 'CZ', 'czechia': 'CZ', 'tschechien': 'CZ', 'tschechische republik': 'CZ',
    # HU
    'hu': 'HU', 'hun': 'HU', 'hungary': 'HU', 'ungarn': 'HU',
    # RO
    'ro': 'RO', 'rou': 'RO', 'romania': 'RO', 'rumänien': 'RO', 'rumaenien': 'RO',
    # BG
    'bg': 'BG', 'bgr': 'BG', 'bulgaria': 'BG', 'bulgarien': 'BG',
    # SK
    'sk': 'SK', 'svk': 'SK', 'slovakia': 'SK', 'slowakei': 'SK',
    # SI
    'si': 'SI', 'svn': 'SI', 'slovenia': 'SI', 'slowenien': 'SI',
    # HR
    'hr': 'HR', 'hrv': 'HR', 'croatia': 'HR', 'kroatien': 'HR',
    # UA
    'ua': 'UA', 'ukr': 'UA', 'ukraine': 'UA',
    # NZ
    'nz': 'NZ', 'nzl': 'NZ', 'new zealand': 'NZ', 'neuseeland': 'NZ',
    # KR
    'kr': 'KR', 'kor': 'KR', 'south korea': 'KR', 'südkorea': 'KR', 'suedkorea': 'KR', 'korea': 'KR',
    # SG
    'sg': 'SG', 'sgp': 'SG', 'singapore': 'SG', 'singapur': 'SG',
    # ID
    'id': 'ID', 'idn': 'ID', 'indonesia': 'ID', 'indonesien': 'ID',
    # MY
    'my': 'MY', 'mys': 'MY', 'malaysia': 'MY',
    # TH
    'th': 'TH', 'tha': 'TH', 'thailand': 'TH',
    # VN
    'vn': 'VN', 'vnm': 'VN', 'vietnam': 'VN',
    # PH
    'ph': 'PH', 'phl': 'PH', 'philippines': 'PH', 'philippinen': 'PH',
    # PK
    'pk': 'PK', 'pak': 'PK', 'pakistan': 'PK',
    # IL
    'il': 'IL', 'isr': 'IL', 'israel': 'IL',
    # SA
    'sa': 'SA', 'sau': 'SA', 'saudi arabia': 'SA', 'saudi-arabien': 'SA', 'saudi arabien': 'SA',
    # AE
    'ae': 'AE', 'are': 'AE', 'united arab emirates': 'AE', 'vereinigte arabische emirate': 'AE', 'uae': 'AE',
    # LU
    'lu': 'LU', 'lux': 'LU', 'luxembourg': 'LU', 'luxemburg': 'LU',
    # LI
    'li': 'LI', 'lie': 'LI', 'liechtenstein': 'LI',
    # IS
    'is': 'IS', 'isl': 'IS', 'iceland': 'IS', 'island': 'IS',
}

def clean_country(val):
    if pd.isna(val):
        return 'UNKNOWN'
    s = str(val).strip().lower()
    if not s:
        return 'UNKNOWN'
    if s in country_map:
        return country_map[s]
    s_no_dot = s.replace('.', '').strip()
    if s_no_dot in country_map:
        return country_map[s_no_dot]
    s_space = s_no_dot.replace('-', ' ').strip()
    if s_space in country_map:
        return country_map[s_space]
    s_hyphen = s_no_dot.replace(' ', '-').strip()
    if s_hyphen in country_map:
        return country_map[s_hyphen]
    return 'UNKNOWN'

df['country'] = df['country'].apply(clean_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)