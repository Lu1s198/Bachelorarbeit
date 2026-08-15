import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google_r3/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

country_map = {
    'de': 'DE', 'deu': 'DE', 'ger': 'DE', 'germany': 'DE', 'deutschland': 'DE', 'brd': 'DE', 'd': 'DE',
    'at': 'AT', 'aut': 'AT', 'austria': 'AT', 'österreich': 'AT', 'oesterreich': 'AT', 'oe': 'AT',
    'ch': 'CH', 'che': 'CH', 'sui': 'CH', 'switzerland': 'CH', 'schweiz': 'CH', 'suisse': 'CH', 'svizzera': 'CH',
    'us': 'US', 'usa': 'US', 'united states': 'US', 'united states of america': 'US', 'vereinigte staaten': 'US', 'vereinigte staaten von amerika': 'US',
    'gb': 'GB', 'gbr': 'GB', 'uk': 'GB', 'united kingdom': 'GB', 'great britain': 'GB', 'großbritannien': 'GB', 'grossbritannien': 'GB', 'england': 'GB',
    'fr': 'FR', 'fra': 'FR', 'france': 'FR', 'frankreich': 'FR',
    'it': 'IT', 'ita': 'IT', 'italy': 'IT', 'italien': 'IT',
    'es': 'ES', 'esp': 'ES', 'spain': 'ES', 'spanien': 'ES',
    'nl': 'NL', 'nld': 'NL', 'netherlands': 'NL', 'niederlande': 'NL', 'holland': 'NL',
    'be': 'BE', 'bel': 'BE', 'belgium': 'BE', 'belgien': 'BE',
    'pl': 'PL', 'pol': 'PL', 'poland': 'PL', 'polen': 'PL',
    'cz': 'CZ', 'cze': 'CZ', 'czech republic': 'CZ', 'czechia': 'CZ', 'tschechien': 'CZ', 'tschechische republik': 'CZ',
    'dk': 'DK', 'dnk': 'DK', 'denmark': 'DK', 'dänemark': 'DK', 'daenemark': 'DK',
    'se': 'SE', 'swe': 'SE', 'sweden': 'SE', 'schweden': 'SE',
    'no': 'NO', 'nor': 'NO', 'norway': 'NO', 'norwegen': 'NO',
    'fi': 'FI', 'fin': 'FI', 'finland': 'FI', 'finnland': 'FI',
    'ie': 'IE', 'irl': 'IE', 'ireland': 'IE', 'irland': 'IE',
    'pt': 'PT', 'prt': 'PT', 'portugal': 'PT',
    'gr': 'GR', 'grc': 'GR', 'greece': 'GR', 'griechenland': 'GR',
    'tr': 'TR', 'tur': 'TR', 'turkey': 'TR', 'türkei': 'TR', 'tuerkei': 'TR',
    'cn': 'CN', 'chn': 'CN', 'china': 'CN',
    'jp': 'JP', 'jpn': 'JP', 'japan': 'JP',
    'in': 'IN', 'ind': 'IN', 'india': 'IN', 'indien': 'IN',
    'br': 'BR', 'bra': 'BR', 'brazil': 'BR', 'brasilien': 'BR',
    'ca': 'CA', 'can': 'CA', 'canada': 'CA', 'kanada': 'CA',
    'au': 'AU', 'aus': 'AU', 'australia': 'AU', 'australien': 'AU',
    'ru': 'RU', 'rus': 'RU', 'russia': 'RU', 'russland': 'RU',
    'mx': 'MX', 'mex': 'MX', 'mexico': 'MX', 'mexiko': 'MX',
    'za': 'ZA', 'zaf': 'ZA', 'south africa': 'ZA', 'südafrika': 'ZA', 'suedafrika': 'ZA',
    'kr': 'KR', 'kor': 'KR', 'south korea': 'KR', 'südkorea': 'KR', 'suedkorea': 'KR', 'korea': 'KR',
    'nz': 'NZ', 'nzl': 'NZ', 'new zealand': 'NZ', 'neuseeland': 'NZ',
    'lu': 'LU', 'lux': 'LU', 'luxembourg': 'LU', 'luxemburg': 'LU',
    'li': 'LI', 'lie': 'LI', 'liechtenstein': 'LI',
    'hr': 'HR', 'hrv': 'HR', 'croatia': 'HR', 'kroatien': 'HR',
    'hu': 'HU', 'hun': 'HU', 'hungary': 'HU', 'ungarn': 'HU',
    'ro': 'RO', 'rou': 'RO', 'romania': 'RO', 'rumänien': 'RO', 'rumaenien': 'RO',
    'sk': 'SK', 'svk': 'SK', 'slovakia': 'SK', 'slowakei': 'SK',
    'si': 'SI', 'svn': 'SI', 'slovenia': 'SI', 'slowenien': 'SI',
    'ua': 'UA', 'ukr': 'UA', 'ukraine': 'UA',
    'bg': 'BG', 'bgr': 'BG', 'bulgaria': 'BG', 'bulgarien': 'BG',
    'is': 'IS', 'isl': 'IS', 'iceland': 'IS', 'island': 'IS',
    'ee': 'EE', 'est': 'EE', 'estonia': 'EE', 'estland': 'EE',
    'lv': 'LV', 'lva': 'LV', 'latvia': 'LV', 'lettland': 'LV',
    'lt': 'LT', 'ltu': 'LT', 'lithuania': 'LT', 'litauen': 'LT',
    'cy': 'CY', 'cyp': 'CY', 'cyprus': 'CY', 'zypern': 'CY',
    'mt': 'MT', 'mlt': 'MT', 'malta': 'MT'
}

def clean_country(val):
    if pd.isna(val) or val is None:
        return 'UNKNOWN'
    s = str(val).strip().lower().rstrip('.')
    return country_map.get(s, 'UNKNOWN')

df['country'] = df['country'].apply(clean_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)