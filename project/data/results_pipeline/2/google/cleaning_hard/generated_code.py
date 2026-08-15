import os
import pandas as pd

input_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google/cleaning_medium/output.parquet"
output_path = r"C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/2/google/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

mapping = {
    'de': 'DE', 'ger': 'DE', 'deu': 'DE', 'germany': 'DE', 'deutschland': 'DE', 'bundesrepublik deutschland': 'DE', 'dt': 'DE',
    'at': 'AT', 'aut': 'AT', 'austria': 'AT', 'österreich': 'AT', 'oesterreich': 'AT',
    'ch': 'CH', 'che': 'CH', 'switzerland': 'CH', 'schweiz': 'CH', 'suisse': 'CH', 'svizzera': 'CH',
    'us': 'US', 'usa': 'US', 'united states': 'US', 'united states of america': 'US', 'vereinigte staaten': 'US', 'vereinigte staaten von amerika': 'US',
    'gb': 'GB', 'gbr': 'GB', 'uk': 'GB', 'united kingdom': 'GB', 'great britain': 'GB', 'großbritannien': 'GB', 'grossbritannien': 'GB', 'england': 'GB',
    'fr': 'FR', 'fra': 'FR', 'france': 'FR', 'frankreich': 'FR',
    'it': 'IT', 'ita': 'IT', 'italy': 'IT', 'italien': 'IT',
    'es': 'ES', 'esp': 'ES', 'spain': 'ES', 'spanien': 'ES',
    'nl': 'NL', 'nld': 'NL', 'netherlands': 'NL', 'niederlande': 'NL', 'holland': 'NL',
    'be': 'BE', 'bel': 'BE', 'belgium': 'BE', 'belgien': 'BE',
    'pl': 'PL', 'pol': 'PL', 'poland': 'PL', 'polen': 'PL',
    'cz': 'CZ', 'cze': 'CZ', 'czech republic': 'CZ', 'czechia': 'CZ', 'tschechien': 'CZ',
    'dk': 'DK', 'dnk': 'DK', 'denmark': 'DK', 'dänemark': 'DK', 'daenemark': 'DK',
    'se': 'SE', 'swe': 'SE', 'sweden': 'SE', 'schweden': 'SE',
    'no': 'NO', 'nor': 'NO', 'norway': 'NO', 'norwegen': 'NO',
    'fi': 'FI', 'fin': 'FI', 'finland': 'FI', 'finnland': 'FI',
    'ie': 'IE', 'irl': 'IE', 'ireland': 'IE', 'irland': 'IE',
    'pt': 'PT', 'prt': 'PT', 'portugal': 'PT',
    'gr': 'GR', 'grc': 'GR', 'greece': 'GR', 'griechenland': 'GR',
    'tr': 'TR', 'tur': 'TR', 'turkey': 'TR', 'türkei': 'TR', 'tuerkei': 'TR', 'türkiye': 'TR',
    'ru': 'RU', 'rus': 'RU', 'russia': 'RU', 'russland': 'RU',
    'cn': 'CN', 'chn': 'CN', 'china': 'CN',
    'jp': 'JP', 'jpn': 'JP', 'japan': 'JP',
    'in': 'IN', 'ind': 'IN', 'india': 'IN', 'indien': 'IN',
    'br': 'BR', 'bra': 'BR', 'brazil': 'BR', 'brasilien': 'BR',
    'ca': 'CA', 'can': 'CA', 'canada': 'CA', 'kanada': 'CA',
    'au': 'AU', 'aus': 'AU', 'australia': 'AU', 'australien': 'AU',
    'za': 'ZA', 'zaf': 'ZA', 'south africa': 'ZA', 'südafrika': 'ZA', 'suedafrika': 'ZA',
    'mx': 'MX', 'mex': 'MX', 'mexico': 'MX', 'mexiko': 'MX',
    'ar': 'AR', 'arg': 'AR', 'argentina': 'AR', 'argentinien': 'AR',
    'cl': 'CL', 'chl': 'CL', 'chile': 'CL',
    'co': 'CO', 'col': 'CO', 'colombia': 'CO', 'kolumbien': 'CO',
    'eg': 'EG', 'egy': 'EG', 'egypt': 'EG', 'ägypten': 'EG', 'aegypten': 'EG',
    'th': 'TH', 'tha': 'TH', 'thailand': 'TH',
    'vn': 'VN', 'vnm': 'VN', 'vietnam': 'VN',
    'kr': 'KR', 'kor': 'KR', 'south korea': 'KR', 'südkorea': 'KR', 'suedkorea': 'KR', 'korea': 'KR',
    'id': 'ID', 'idn': 'ID', 'indonesia': 'ID', 'indonesien': 'ID',
    'my': 'MY', 'mys': 'MY', 'malaysia': 'MY',
    'sg': 'SG', 'sgp': 'SG', 'singapore': 'SG', 'singapur': 'SG',
    'nz': 'NZ', 'nzl': 'NZ', 'new zealand': 'NZ', 'neuseeland': 'NZ',
    'ua': 'UA', 'ukr': 'UA', 'ukraine': 'UA',
    'ro': 'RO', 'rou': 'RO', 'romania': 'RO', 'rumänien': 'RO', 'rumaenien': 'RO',
    'hu': 'HU', 'hun': 'HU', 'hungary': 'HU', 'ungarn': 'HU',
    'sk': 'SK', 'svk': 'SK', 'slovakia': 'SK', 'slowakei': 'SK',
    'si': 'SI', 'svn': 'SI', 'slovenia': 'SI', 'slowenien': 'SI',
    'hr': 'HR', 'hrv': 'HR', 'croatia': 'HR', 'kroatien': 'HR',
    'bg': 'BG', 'bgr': 'BG', 'bulgaria': 'BG', 'bulgarien': 'BG',
    'lu': 'LU', 'lux': 'LU', 'luxembourg': 'LU', 'luxemburg': 'LU',
    'li': 'LI', 'lie': 'LI', 'liechtenstein': 'LI',
    'is': 'IS', 'isl': 'IS', 'iceland': 'IS', 'island': 'IS',
    'ee': 'EE', 'est': 'EE', 'estonia': 'EE', 'estland': 'EE',
    'lv': 'LV', 'lva': 'LV', 'latvia': 'LV', 'lettland': 'LV',
    'lt': 'LT', 'ltu': 'LT', 'lithuania': 'LT', 'litauen': 'LT',
}

def clean_country(val):
    if pd.isna(val):
        return 'UNKNOWN'
    val_str = str(val).strip().lower()
    return mapping.get(val_str, 'UNKNOWN')

df['country'] = df['country'].apply(clean_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)