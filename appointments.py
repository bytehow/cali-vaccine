import time
import traceback
import argparse
from datetime import date, datetime, timedelta
from pprint import pprint

import requests
import pytz
from tweet import TwitterHandler, TWITTER_TWEET_LIMIT
from colorama import Fore, Back, Style

SAN_DIEGO = 'San Diego'
LOS_ANGELES = 'Los Angeles'
BAY_AREA = 'Bay Area'

GEOCODES = {
    # lat, lng
    BAY_AREA: [
        (37.752483,-122.19821), # Oakland Colisium
        (37.784323,-122.40069), # Moscone Center
        (37.338208,-121.886329), # San Jose
    ],
    LOS_ANGELES: [
        (34.173598,-118.503011), # Balboa Sports Complex
        (34.07504,-118.181976), # El Sereno Recreation Center
        (34.085815,-117.76796), # SD 1 - Pomona Fairplex
        (33.958085,-118.342062), # SD2-The Forum
        (34.239936,-118.526252), # SD3-CSUN
        (33.916392,-118.129275), # SD4-LA County Office of Education
        (34.421362,-118.589395), # SD5-Six Flags Magic Mountain
        (34.073851,-118.239958), # Dodger Stadium
        (33.967775,-118.291751), # Crenshaw Christian Center
        (34.271363,-118.38976), # Hansen Dam Recreational Center
        (34.065426,-118.205902), # Lincoln Park
        (34.280941,-118.433971), # San Fernando Park
        (34.398955,-118.551109), # Henry Mayo
        (34.096322,-118.290301), # Hollywood Presbyterian
        (33.923177,-118.2438), # Martin Luther King Community Hospital
        (33.892993,-118.295005), # Memorial Hospital of Gardena
        (33.96903,-118.049072), # PIH Whittier
        (34.097893,-118.289632), # CHLA
        (33.811895,-118.343547), # Torrance Memorial
        (33.82984,-118.294736), # DHS Harbor-UCLA Medical Center
        (34.325965,-118.44616), # UCLA Olive View
        (34.047489,-118.21684), # LAC+USC Medical Center
        (33.929332,-118.158588), # Rancho los amigos
        (34.07611,-118.379999), # Cedars
        (34.062488,-118.202722), # Keck Medicine
        (34.069532,-118.263489), # LA Downtown Medical Center
        (34.189532,-118.450682), # SCMC ??
        (33.339161,-118.330716), # Catalina medical island
    ],
    SAN_DIEGO: [
        (32.700958,-117.126016), # Central Region Immunization Clinic
        (32.672315,-117.10377), # Martin Luther King Community Center- Janssen
        (32.710125,-117.084695), # Tubman-Chavez Community Center
        (32.755407,-117.101196), # Copley-Price YMCA
        (32.740031,-117.029802), # Lemon Grove Community Center
        (32.606372,-117.085752), # South Region Live Well Center at Chula Vista
        (32.576672,-117.121752), # Mar Vista High School
        (32.57815,-117.05707), # Border View YMCA - Janssen
        (32.555746,-117.05417), # San Ysidro Southwestern College
        (32.798785,-116.960557), # East Public Health Center
        (32.973742,-117.260998), # North Coastal – Scripps Del Mar Fairgrounds Park Super Station
        (33.12486,-117.075823), # Palomar Medical Center Downtown Escondido
        (33.131983,-117.157541), # San Marcos Vaccine Super Station at Cal State University San Marcos (CSUSM), Sports Center
        (33.2081,-117.245749), # Linda Rhoades Recreation Center
        (33.211189,-117.311218), # North Coastal Live Well Center
    ],
}

STATE = {}
PROXIES = {
    'http': 'http://localhost:24000',
    'https': 'http://localhost:24000',
}

PROXY_HOST='localhost'
PROXY_TIMEOUT_EXPIRATION=None
PROXY_TIMEOUT_MINUTES=60

TWITTER_ACCOUNTS = {
    LOS_ANGELES: TwitterHandler('CovidVaccineLA'),
    BAY_AREA: TwitterHandler('CovidVaccineBA'),
    SAN_DIEGO: TwitterHandler('CovidVaccineSD'),
    'PRIMARY': TwitterHandler('CovidVaccineCA'),
}

DEFAULT_MIN_APPTS = 5
MIN_APPTS = {
    LOS_ANGELES: DEFAULT_MIN_APPTS,
    BAY_AREA: 2,
    SAN_DIEGO: DEFAULT_MIN_APPTS,
}

for key in GEOCODES.keys():
    STATE[key] = {'current': -1, 'max': -1, 'start': None, 'end': None}

def make_proxied_request(method, url, always_proxy=False, **kwargs):
    global PROXY_TIMEOUT_EXPIRATION
    global PROXY_TIMEOUT_MINUTES

    try:
        if always_proxy or (PROXY_TIMEOUT_EXPIRATION and datetime.now() < PROXY_TIMEOUT_EXPIRATION):
            if PROXY_TIMEOUT_EXPIRATION:
                print(f'Using proxy till {PROXY_TIMEOUT_EXPIRATION}. It is now {datetime.now()}')

            return requests.request(method, url, proxies=PROXIES,  **kwargs)

        resp = requests.request(method, url, **kwargs)

        # Try with proxy
        if (resp.status_code == 403):
            PROXY_TIMEOUT_EXPIRATION = datetime.now() + timedelta(minutes=PROXY_TIMEOUT_MINUTES)

            print('Got 403. Using proxy')
            resp = requests.request(method, url, proxies=PROXIES, **kwargs)
        else:
            PROXY_TIMEOUT_EXPIRATION = None

    except Exception:
        error_str = traceback.format_exc()
        print(f'Proxy failed for {method} {url}')
        print(Fore.RED + error_str + Style.RESET_ALL)
        return None

    return resp

def get_locations(location_group):
    locations = {}

    # Generated by burp
    url = "https://api.myturn.ca.gov:443/public/locations/search"
    headers = {"goodbot": "j4ebLPKpkFt4ueEsaeQaY6PV", "Connection": "close", "User-Agent": "TwitterVaccineBot", "Content-Type": "application/json;charset=UTF-8", "Origin": "https://myturn.ca.gov", "Sec-Fetch-Site": "same-site", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://myturn.ca.gov/", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US,en;q=0.9"}

    for lat, lng in GEOCODES[location_group]:
        today = str(date.today())
        payload={"doseNumber": 1, "fromDate": today, "location": {"lat": lat, "lng": lng}, "locationQuery": {"includePools": ["default"]}, "url": "https://myturn.ca.gov/location-select", "vaccineData": "WyJhM3F0MDAwMDAwMEN5SkJBQTAiLCJhM3F0MDAwMDAwMDFBZExBQVUiLCJhM3F0MDAwMDAwMDFBZE1BQVUiLCJhM3F0MDAwMDAwMDFBZ1VBQVUiLCJhM3F0MDAwMDAwMDFBZ1ZBQVUiLCJhM3F0MDAwMDAwMDFBc2FBQUUiXQ=="}

        res = make_proxied_request('POST', url, headers=headers, json=payload)
        if not res:
            continue

        res.raise_for_status()
        res_json = res.json()

        if not res_json['locations']:
            continue

        for loc in res_json['locations']:
            if loc['type'] != 'OnlineBooking':
                continue

            id = loc['extId']
            name = loc['name']
            address = loc['displayAddress']
            vaccine_data = loc['vaccineData']
            if id in locations:
                continue

            locations[id] = { 'id': id, 'name': name, 'address': address , 'vaccine_data': vaccine_data}

    return locations

def get_appt_days(id, vaccine_data, start, end, dose=1):
    # Generated by burp
    burp0_url = f"https://api.myturn.ca.gov:443/public/locations/{id}/availability"
    burp0_headers = {"goodbot": "j4ebLPKpkFt4ueEsaeQaY6PV", "Connection": "close", "User-Agent": "TwitterVaccineBot", "Content-Type": "application/json;charset=UTF-8", "Origin": "https://myturn.ca.gov", "Sec-Fetch-Site": "same-site", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://myturn.ca.gov/", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US,en;q=0.9"}
    burp0_json={"doseNumber": dose, "endDate": str(end), "startDate": str(start), "url": "https://myturn.ca.gov/appointment-select", "vaccineData": vaccine_data}

    resp = make_proxied_request('POST', burp0_url, headers=burp0_headers, json=burp0_json)
    if not resp:
        return []

    resp.raise_for_status()
    resp_json = resp.json()

    appts = [apt['date'] for apt in resp_json['availability'] if apt['available']]
    return appts

def get_slots(id, vaccine_data, day):
    burp0_url = f"https://api.myturn.ca.gov:443/public/locations/{id}/date/{day}/slots"
    burp0_headers = {"goodbot": "j4ebLPKpkFt4ueEsaeQaY6PV", "Connection": "close", "User-Agent": "TwitterVaccineBot", "Content-Type": "application/json;charset=UTF-8", "Origin": "https://myturn.ca.gov", "Sec-Fetch-Site": "same-site", "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty", "Referer": "https://myturn.ca.gov/", "Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US,en;q=0.9"}
    burp0_json={"url": "https://myturn.ca.gov/appointment-select", "vaccineData": vaccine_data}
    resp = make_proxied_request('POST', burp0_url, headers=burp0_headers, json=burp0_json)
    if not resp:
        return []

    resp.raise_for_status()
    resp_json = resp.json()

    slots = [datetime.strptime(slot['localStartTime'], '%H:%M:%S').strftime('%I:%M %p') for slot in resp_json['slotsWithAvailability']]
    return slots

def get_location_appts(locations, start, end):
    today = str(date.today())
    appts = {}
    for loc in locations.values():
        # Get first appointments
        first_appt_days = get_appt_days(loc['id'], loc['vaccine_data'], start, end, dose=1)
        first_slots = {}

        # Get appointment times
        for first_dose_day_str in first_appt_days:
            # Appointments have to be in the future, so we need to filter out slots that are already passed
            first_dose_slots = get_slots(loc['id'], loc['vaccine_data'], first_dose_day_str)
            if first_dose_day_str == today:
                filtered_slots = []
                for s in first_dose_slots:
                    slot = datetime.strptime(first_dose_day_str + s, '%Y-%m-%d%I:%M %p')
                    if slot > datetime.now():
                        filtered_slots.append(slot.strftime('%I:%M %p'))

                first_dose_slots = filtered_slots

            if not first_dose_slots:
                continue

            first_slots[first_dose_day_str] = sorted(first_dose_slots)
            appts[loc['id']] = first_slots

    return appts

def format_appointments(locations, appointments):
    for id, appts in appointments.items():
        name = locations[id]['name']
        print(f'Appointments for {name} ({id}):')
        print(Fore.CYAN)
        pprint(appts)

        print('')
        print(Style.RESET_ALL)

def get_total_appointments(appointments):
    total = 0
    start = None
    end = None
    for appts in appointments.values():
        # Figure out earliest and latest appointment days
        for d, slots in appts.items():
            if not slots:
                continue

            total += len(slots)
            day = datetime.strptime(d, '%Y-%m-%d')
            if not start:
                start = day
            else:
                start = min([start, day])

            if not end:
                end = day
            else:
                end = max([end, day])

    return total, start, end

def get_group_appointments(location_group, start, end):
    print('*' * 100)
    print(f'{Fore.YELLOW}Getting {location_group} availability{Style.RESET_ALL}')
    print('*' * 100)

    locations = get_locations(location_group)
    
    appts = get_location_appts(locations, start, end)
    total, start, end = get_total_appointments(appts)
    return locations, appts, total, start, end

def print_appointments(location_group, locations, appts, total, start, end, print_slots=False):
    if total == 0:
        color = Fore.RED
    elif total <= 10:
        color = Fore.YELLOW
    else:
        color = Fore.GREEN

    print(f'{color} {location_group} has at least {total} available appointments between {start} - {end}{Style.RESET_ALL}')

    if total and print_slots:
        print('-----Listing slots:')
        format_appointments(locations, appts)

    print(Style.RESET_ALL)

def get_timestamp():
    tz = pytz.timezone('US/Pacific')
    t = datetime.now(tz).strftime("%I:%M %p")
    return f'({t})'

def get_summary_tweet(location_group, total, start, end):
    prev = STATE[location_group]['current'] 
    prev_max = STATE[location_group]['max'] 
    prev_start = STATE[location_group]['start'] 
    prev_end = STATE[location_group]['end'] 
    STATE[location_group]['current'] = total
    STATE[location_group]['start'] = start
    STATE[location_group]['end'] = end

    # Reset max if previous appointments are out
    if total == 0:
        STATE[location_group]['max'] = 0
    else:
        STATE[location_group]['max'] = max([prev_max, total])

    print('-----stats:')
    pprint(STATE[location_group])

    # Never had appointments
    if (prev <= 0 and total > 0) or (total > 0 and (prev_start != start or prev_end != end)) :
        if start == end:
            tweet = f'{location_group} has at least {total} appointments on {start} 🙌\nBook one now at myturn.ca.gov!'
        else:
            tweet = f'{location_group} has at least {total} appointments between {start} - {end} 🙌\nBook one now at myturn.ca.gov!'
    elif total > prev_max and prev_max > 0:
        diff = total - prev_max
        if start == end:
            tweet = f'{location_group} added {diff} appointments 🤩\nThere are now at least {total} appointments on {start}\nBook one at myturn.ca.gov!'
        else:
            tweet = f'{location_group} added {diff} appointments 🤩\nThere are now at least {total} appointments between {start} - {end}\nBook one at myturn.ca.gov!'
    else:
        tweet = None

    # Add a seasrchable hashtag
    if tweet:
        location_tag = f'#{location_group.replace(" ", "")}Appts'
        timestamp = get_timestamp()
        return f'{timestamp} {tweet} #TeamVaccine {location_tag}\n\nLocation details below 🧵'
    else:
        return None

def get_location_tweets(locations, appointments, min_appts):
    tweets = []
    for id, appts in appointments.items():
        total = 0
        name = locations[id]['name']
        address = locations[id]['address']

        # Figure out earliest and latest day for this location
        start = None
        end = None
        for d, slots in appts.items():
            if not slots:
                continue

            day = datetime.strptime(d, '%Y-%m-%d')
            if not start:
                start = day
            else:
                start = min([start, day])

            if not end:
                end = day
            else:
                end = max([end, day])

        for slots in appts.values():
            total += len(slots)

        if total < min_appts:
            continue

        start = start.strftime('%m-%d-%Y')
        end = end.strftime('%m-%d-%Y')

        timestamp = get_timestamp()

        to_trim = 1
        while True:
            tweet = ''
            if start == end:
                if (total > 1):
                    tweet += f'{timestamp} {total} of them on {start}'
                else:
                    tweet += f'{timestamp} {total} on {start}'
            else:
                if (total > 1):
                    tweet += f'{timestamp} {total} of them between {start} - {end}'
                else:
                    # Should never happen
                    tweet += f'{timestamp} {total} on {start} or {end}'

            tweet += f' when selecting 👇\n\n"{name}"\n{address}\n\n🚨MyTurn is buggy! These may not be available!🚨'

            # Trim if we're over the lemit
            if len(tweet) > TWITTER_TWEET_LIMIT:
                name = locations[id]['name'][:-(to_trim + 3)]
                name += '...'
                to_trim += 1
            else:
                break

        tweets.append(tweet)

    return tweets

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-tweet', 
        help='Dont send out tweets',
        action='store_true',
        required=False,
    )

    parser.add_argument('--no-error', 
        help='Dont send error message DMs',
        action='store_true',
        required=False,
    )

    args = parser.parse_args()

    primary_handler = TWITTER_ACCOUNTS['PRIMARY']

    while(True):
        for group in GEOCODES.keys():
            region_handler = TWITTER_ACCOUNTS[group]
            try:
                search_start = date.today()
                search_end = search_start + timedelta(days=8)
                locations, appts, total, appt_start, appt_end = get_group_appointments(group, search_start, search_end)

                min_appts = MIN_APPTS[group]
                if total > 0 and total < min_appts:
                    print(f'{group} has {total} appointments, which is less than min of {min_appts}. Skipping.')
                    continue

                if total:
                    start = appt_start.strftime('%m-%d-%Y')
                    end = appt_end.strftime('%m-%d-%Y')
                else:
                    start = search_start.strftime('%m-%d-%Y')
                    end = search_end.strftime('%m-%d-%Y')

                print_appointments(group, locations, appts, total, start, end, print_slots=True)
                print('Generating tweet:')
                print('-'* 10)

                tweet = get_summary_tweet(group, total, start, end)

                if tweet:
                    location_tweets = get_location_tweets(locations, appts, min_appts)
                    tweets = [tweet, *location_tweets]

                    # Only tweet if there's locations that meet the minimum
                    if len(tweets) == 1:
                        continue

                    for t in tweets:
                        print(Fore.LIGHTMAGENTA_EX + t.replace('\n', '\n' + Fore.LIGHTMAGENTA_EX ) + Style.RESET_ALL)
                        print(f'Tweet was {len(t)} long')

                    if not args.no_tweet:
                        thread = region_handler.tweet_thread(tweets)
                        primary_handler.retweet(thread.id)
                else:
                    print('<last tweet is still accurate. not tweeting>')
                print('-'* 10)
            except Exception:
                error_str = traceback.format_exc()
                if not args.no_error:
                    primary_handler.dm(error_str)

                print(Fore.RED + error_str + Style.RESET_ALL)

        sleep = 60 * 5
        print(f'Sleeping {sleep} seconds...')
        time.sleep(sleep)

main()
