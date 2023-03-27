import cloudscraper
import pandas as pd
from bs4 import BeautifulSoup
from latest_user_agents import get_random_user_agent
import json
from datetime import datetime

def get_organiser(organiser_link):
    item_list = []
    scraper = cloudscraper.create_scraper()
    ua = get_random_user_agent()
    headers = {
        'User-Agent': ua
    }
    response = scraper.get(organiser_link, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')
    box = soup.select_one('div[data-testid="organizer-profile__future-events"]')
    cards = box.select('div[data-testid="organizer-profile__events"] .organizer-profile__event-renderer__grid .eds-event-card--consumer')
    for card in cards:
        event_link = card.select_one('a')['href']
        items = event_scraper(event_link)
        item_list.append(items)

    df = pd.DataFrame(item_list)
    df.to_csv('sample_data.csv', index=False)

def get_data(json_data, image_url):
    data = json.loads(json_data, strict=False)
    organiser_name = data['organizer']['displayOrganizationName']
    event_name = data['event']['name']
    start_date = data['event']['start']['utc']
    start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ')
    s_time = start_date.time().isoformat()
    s_date = start_date.date().isoformat()
    end_date = data['event']['end']['utc']
    end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ')
    e_time = end_date.time().isoformat()
    e_date = end_date.date().isoformat()
    event_url = data['event']['url']
    event_description = data['components']['eventDescription']['summary']
    event_fee = data['components']['conversionBar']['panelDisplayPrice']
    is_online = data['event']['isOnlineEvent']
    if not is_online:
        address = data['components']['eventMap']['venueAddress']
        venueName = data['components']['eventMap']['venueName']
        event_country = data['event']['venue']['country']
        event_region = data['event']['venue']['region']
    else:
        address = None
        venueName = 'Online'
        event_country = None
        event_region = None

    items = {
        'Organiser Name': organiser_name,
        'Event Name': event_name,
        'Start Date': s_date,
        'Start Time': s_time,
        'End Date': e_date,
        'End Time': e_time,
        'Event Fee': event_fee,
        'Event Description': event_description,
        'Event URL': event_url,
        'Event Image': image_url,
        'Address': address,
        'Venue': venueName,
        'Event Country': event_country,
        'Event Region': event_region
    }
    return items

def event_scraper(event_link):
    scraper = cloudscraper.create_scraper()
    ua = get_random_user_agent()
    headers = {
        'User-Agent': ua
    }
    response = scraper.get(event_link, headers=headers)
    soup = BeautifulSoup(response.text, 'lxml')
    all_scripts = soup.select('script')
    for script in all_scripts:
        if 'window.__SERVER_DATA__' in script.text:
            data_script = script
    json_data = data_script.text.strip().replace('window.__SERVER_DATA__ = ', '').replace(';', '')
    try:
        image_url = soup.select_one('picture img')['src']
    except:
        image_url = None
    items = get_data(json_data, image_url)
    return items

get_organiser('https://www.eventbrite.com/o/moxy-east-village-33800767649')
