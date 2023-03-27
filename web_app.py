import cloudscraper
import pandas as pd
from bs4 import BeautifulSoup
from latest_user_agents import get_random_user_agent
import json
from datetime import datetime
import streamlit as st
from time import sleep


@st.cache_data
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

def downlaod_csv(df):
    csv = convert_df(df)
    st.download_button(
    "Press to Download the csv data",
    csv,
    "event_data.csv",
    "text/csv",
    key='download-csv'
    )

def get_organiser(organiser_link):
    item_list = []
    y = 0
    col1, col2 = st.columns(2)
    progress = col1.metric('Event scraped', 0)
    for link in organiser_link:
        sleep(2)
        scraper = cloudscraper.create_scraper()
        ua = get_random_user_agent()
        headers = {
            'User-Agent': ua
        }
        response = scraper.get(link, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        try:
            box = soup.select_one('div[data-testid="organizer-profile__future-events"]')
            cards = box.select('div[data-testid="organizer-profile__events"] .organizer-profile__event-renderer__grid .eds-event-card--consumer')
            for card in cards:
                y = y + 1
                event_link = card.select_one('a')['href']
                items = event_scraper(event_link)
                item_list.append(items)
                progress.metric('Event scraped', y)
        except:
            st.warning(f'No Upcoming event for this organizer: {link}')

    df = pd.DataFrame(item_list)
    col2.metric('Total Event scrape', len(df))
    st.dataframe(df)
    #df.to_csv('sample_data.csv', index=False)
    downlaod_csv(df)

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
    event_image = image_url
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
        'Event Image': event_image,
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


import streamlit as st

def main():
    st.set_page_config(
        page_title="EVENTBRITE EVENT SCRAPER 🎈",
        page_icon=":balloon:",
        layout="wide"
    )

    #st.image("banner.png", use_column_width=True)

    st.title('EVENTBRITE EVENT SCRAPER 🎈')
    st.info('''
    Paste an organizer URL or URLs and get all the upcoming events. If you are pasting multiple URLs make sure to seperate with (;).
    ''')


    with st.form('scraper form'):
        organiser_links = st.text_area('Organizer URL(s)', placeholder = '''
        https://www.eventbrite.com/o/the-inside-out-wisdom-and-action-project-33736776827;
        https://www.eventbrite.com/o/affordable-art-fair-nyc-16057474978;
        ''')
        organiser_link = organiser_links.split(';')
        scrape = st.form_submit_button('Scrape')

    if scrape:
        with st.spinner('Loading...'):
            get_organiser(organiser_link)
            st.success('Done!')

    # Load custom CSS
    st.markdown("""
        <style>
            body {
                font-family: 'Helvetica Neue', sans-serif;
            }
            .streamlit-button {
                background-color: #FF5722;
                color: #FFFFFF;
            }
        </style>

        <style>
            #MainMenu {
                visibility:hidden;}
            footer {
                visibility:hidden;}
        </style>
    """, unsafe_allow_html=True)

if __name__ == '__main__':
    main()
