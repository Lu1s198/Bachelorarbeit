import os
import re
import pandas as pd
import numpy as np

input_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_medium/output.parquet"
output_path = "C:/Users/geige/Desktop/DHBW/Bachelorarbeit/project/data/results_pipeline/1/google/cleaning_hard/output.parquet"

df = pd.read_parquet(input_path)

COUNTRY_MAP = {
    # Germany
    'de': 'DE', 'deu': 'DE', 'ger': 'DE', 'germany': 'DE', 'deutschland': 'DE', 'd': 'DE', 'allemagne': 'DE', 'brd': 'DE',
    # Austria
    'at': 'AT', 'aut': 'AT', 'austria': 'AT', 'österreich': 'AT', 'oesterreich': 'AT',
    # Switzerland
    'ch': 'CH', 'che': 'CH', 'switzerland': 'CH', 'schweiz': 'CH', 'suisse': 'CH', 'svizzera': 'CH',
    # United States
    'us': 'US', 'usa': 'US', 'united states': 'US', 'united states of america': 'US', 'vereinigte staaten': 'US', 'vereinigte staaten von amerika': 'US', 'vst': 'US', 'vsta': 'US',
    # United Kingdom
    'gb': 'GB', 'gbr': 'GB', 'uk': 'GB', 'united kingdom': 'GB', 'great britain': 'GB', 'großbritannien': 'GB', 'grossbritannien': 'GB', 'england': 'GB', 'scotland': 'GB', 'wales': 'GB',
    # France
    'fr': 'FR', 'fra': 'FR', 'france': 'FR', 'frankreich': 'FR',
    # Italy
    'it': 'IT', 'ita': 'IT', 'italy': 'IT', 'italien': 'IT',
    # Spain
    'es': 'ES', 'esp': 'ES', 'spain': 'ES', 'spanien': 'ES',
    # Netherlands
    'nl': 'NL', 'nld': 'NL', 'netherlands': 'NL', 'niederlande': 'NL', 'holland': 'NL',
    # Belgium
    'be': 'BE', 'bel': 'BE', 'belgium': 'BE', 'belgien': 'BE',
    # Poland
    'pl': 'PL', 'pol': 'PL', 'poland': 'PL', 'polen': 'PL',
    # Czech Republic
    'cz': 'CZ', 'cze': 'CZ', 'czech republic': 'CZ', 'czechia': 'CZ', 'tschechien': 'CZ', 'tschechische republik': 'CZ',
    # Denmark
    'dk': 'DK', 'dnk': 'DK', 'denmark': 'DK', 'dänemark': 'DK', 'daenemark': 'DK',
    # Sweden
    'se': 'SE', 'swe': 'SE', 'sweden': 'SE', 'schweden': 'SE',
    # Norway
    'no': 'NO', 'nor': 'NO', 'norway': 'NO', 'norwegen': 'NO',
    # Finland
    'fi': 'FI', 'fin': 'FI', 'finland': 'FI', 'finnland': 'FI',
    # Portugal
    'pt': 'PT', 'prt': 'PT', 'portugal': 'PT',
    # Greece
    'gr': 'GR', 'grc': 'GR', 'greece': 'GR', 'griechenland': 'GR',
    # Ireland
    'ie': 'IE', 'irl': 'IE', 'ireland': 'IE', 'irland': 'IE',
    # Canada
    'ca': 'CA', 'can': 'CA', 'canada': 'CA', 'kanada': 'CA',
    # Australia
    'au': 'AU', 'aus': 'AU', 'australia': 'AU', 'australien': 'AU',
    # China
    'cn': 'CN', 'chn': 'CN', 'china': 'CN',
    # Japan
    'jp': 'JP', 'jpn': 'JP', 'japan': 'JP',
    # India
    'in': 'IN', 'ind': 'IN', 'india': 'IN', 'indien': 'IN',
    # Brazil
    'br': 'BR', 'bra': 'BR', 'brazil': 'BR', 'brasilien': 'BR',
    # Russia
    'ru': 'RU', 'rus': 'RU', 'russia': 'RU', 'russland': 'RU',
    # Mexico
    'mx': 'MX', 'mex': 'MX', 'mexico': 'MX', 'mexiko': 'MX',
    # Turkey
    'tr': 'TR', 'tur': 'TR', 'turkey': 'TR', 'türkei': 'TR', 'tuerkei': 'TR', 'türkiye': 'TR',
    # South Africa
    'za': 'ZA', 'zaf': 'ZA', 'south africa': 'ZA', 'südafrika': 'ZA', 'suedafrika': 'ZA',
    # New Zealand
    'nz': 'NZ', 'nzl': 'NZ', 'new zealand': 'NZ', 'neuseeland': 'NZ',
    # Luxembourg
    'lu': 'LU', 'lux': 'LU', 'luxembourg': 'LU', 'luxemburg': 'LU',
    # Liechtenstein
    'li': 'LI', 'lie': 'LI', 'liechtenstein': 'LI',
    # Hungary
    'hu': 'HU', 'hun': 'HU', 'hungary': 'HU', 'ungarn': 'HU',
    # Romania
    'ro': 'RO', 'rou': 'RO', 'romania': 'RO', 'rumänien': 'RO', 'rumaenien': 'RO',
    # Bulgaria
    'bg': 'BG', 'bgr': 'BG', 'bulgaria': 'BG', 'bulgarien': 'BG',
    # Slovakia
    'sk': 'SK', 'svk': 'SK', 'slovakia': 'SK', 'slowakei': 'SK',
    # Slovenia
    'si': 'SI', 'svn': 'SI', 'slovenia': 'SI', 'slowenien': 'SI',
    # Croatia
    'hr': 'HR', 'hrv': 'HR', 'croatia': 'HR', 'kroatien': 'HR',
    # Serbia
    'rs': 'RS', 'srb': 'RS', 'serbia': 'RS', 'serbien': 'RS',
    # Ukraine
    'ua': 'UA', 'ukr': 'UA', 'ukraine': 'UA',
    # Belarus
    'by': 'BY', 'blr': 'BY', 'belarus': 'BY', 'weißrussland': 'BY', 'weissrussland': 'BY',
    # Argentina
    'ar': 'AR', 'arg': 'AR', 'argentina': 'AR', 'argentinien': 'AR',
    # Chile
    'cl': 'CL', 'chl': 'CL', 'chile': 'CL',
    # Colombia
    'co': 'CO', 'col': 'CO', 'colombia': 'CO', 'kolumbien': 'CO',
    # Peru
    'pe': 'PE', 'per': 'PE', 'peru': 'PE',
    # Egypt
    'eg': 'EG', 'egy': 'EG', 'egypt': 'EG', 'ägypten': 'EG', 'aegypten': 'EG',
    # Israel
    'il': 'IL', 'isr': 'IL', 'israel': 'IL',
    # United Arab Emirates
    'ae': 'AE', 'are': 'AE', 'united arab emirates': 'AE', 'vae': 'AE', 'uae': 'AE', 'vereinigte arabische emirate': 'AE',
    # Saudi Arabia
    'sa': 'SA', 'sau': 'SA', 'saudi arabia': 'SA', 'saudi-arabien': 'SA', 'saudi arabien': 'SA',
    # Singapore
    'sg': 'SG', 'sgp': 'SG', 'singapore': 'SG', 'singapur': 'SG',
    # South Korea
    'kr': 'KR', 'kor': 'KR', 'south korea': 'KR', 'südkorea': 'KR', 'suedkorea': 'KR', 'korea, south': 'KR', 'korea south': 'KR',
    # North Korea
    'kp': 'KP', 'prk': 'KP', 'north korea': 'KP', 'nordkorea': 'KP',
    # Thailand
    'th': 'TH', 'tha': 'TH', 'thailand': 'TH',
    # Vietnam
    'vn': 'VN', 'vnm': 'VN', 'vietnam': 'VN',
    # Indonesia
    'id': 'ID', 'idn': 'ID', 'indonesia': 'ID', 'indonesien': 'ID',
    # Malaysia
    'my': 'MY', 'mys': 'MY', 'malaysia': 'MY',
    # Philippines
    'ph': 'PH', 'phl': 'PH', 'philippines': 'PH', 'philippinen': 'PH',
    # Pakistan
    'pk': 'PK', 'pak': 'PK', 'pakistan': 'PK',
    # Bangladesh
    'bd': 'BD', 'bgd': 'BD', 'bangladesh': 'BD', 'bangladesch': 'BD',
    # Nigeria
    'ng': 'NG', 'nga': 'NG', 'nigeria': 'NG',
    # Kenya
    'ke': 'KE', 'ken': 'KE', 'kenya': 'KE', 'kenia': 'KE',
    # Morocco
    'ma': 'MA', 'mar': 'MA', 'morocco': 'MA', 'marokko': 'MA',
    # Iceland
    'is': 'IS', 'isl': 'IS', 'iceland': 'IS', 'island': 'IS',
    # Estonia
    'ee': 'EE', 'est': 'EE', 'estonia': 'EE', 'estland': 'EE',
    # Latvia
    'lv': 'LV', 'lva': 'LV', 'latvia': 'LV', 'lettland': 'LV',
    # Lithuania
    'lt': 'LT', 'ltu': 'LT', 'lithuania': 'LT', 'litauen': 'LT',
    # Cyprus
    'cy': 'CY', 'cyp': 'CY', 'cyprus': 'CY', 'zypern': 'CY',
    # Malta
    'mt': 'MT', 'mlt': 'MT', 'malta': 'MT'
}

def standardize_country(val):
    if pd.isna(val):
        return 'UNKNOWN'
    val_str = str(val).strip()
    if not val_str:
        return 'UNKNOWN'
    
    cleaned = val_str.lower()
    cleaned_no_dots = cleaned.replace('.', '')
    
    if cleaned in COUNTRY_MAP:
        return COUNTRY_MAP[cleaned]
    if cleaned_no_dots in COUNTRY_MAP:
        return COUNTRY_MAP[cleaned_no_dots]
    
    cleaned_alpha = re.sub(r'[^a-z0-9\säöüßáéíóúàèìòùâêîôû]', '', cleaned).strip()
    if cleaned_alpha in COUNTRY_MAP:
        return COUNTRY_MAP[cleaned_alpha]
        
    return 'UNKNOWN'

df['country'] = df['country'].apply(standardize_country)

os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_parquet(output_path, index=False)