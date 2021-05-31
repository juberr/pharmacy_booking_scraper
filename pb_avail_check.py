from bs4 import BeautifulSoup as soup
import csv
import requests as req
import re
from urllib import parse
import aiohttp

async def get_calendar_html(session, url):

    # parse the url
    url_dict = parse.parse_qs(parse.urlparse(url).query)
    appointment_type = url_dict['appointmentType'][0]
    owner = url_dict['owner'][0]
    location = url_dict['location'][0]

    # find the calendar code
    url_get = await session.get(url)
    url_html = await url_get.text()
    html_soup = soup(url_html, 'html.parser')
    scripts= str(html_soup.find_all('script')[7])
    
    calendar_code = re.findall(r'typeToCalendars\[{0}] = \[\[(\d+).'.format(appointment_type), scripts)[0]

    # create post body
    post_data = {
    'type': appointment_type,
    'calendar': calendar_code,
    'skip': 'true',
    'options[qty]': 1,
    'options[numDays]': 3,
    'appointmentType': appointment_type
    }

    # create post url
    encoded_location = parse.urlencode({'location':location})
    post_url = f'https://app.acuityscheduling.com/schedule.php?action=showCalendar&fulldate=1&owner={owner}&template=monthly&{encoded_location}'

    calendar_html = await session.post(post_url, data=post_data)

    data = await calendar_html.text()

    return data

def get_pharmbooking_avail(html):

    html = soup(html, 'html.parser')

    avail = html.findAll('td', class_='activeday')

    return bool(avail)

async def get_html_and_avail(session, url):

    html = await get_calendar_html(session, url)

    return (get_pharmbooking_avail(html))





    

