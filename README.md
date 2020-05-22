# Event-scrapper

A web scraping python script to generate an ical calandar file from a list of Facebook events pages.
The goal is to retrieve events without having to spend hours on FB. Unfortunately Facebook has won and the majority of events are announced and shared on FB, even when the bands or venues have their own website. 

Facebook Graph API no longer supports events, so this script uses selenium. The use of selenium and web scarpping in general is contrary to Facebook's terms of use.
If you remain reasonable about the number of pages, the frequency of use, if you don't use selenium in headless mode, tor or other proxy, it shouldn't be a okay. 
If you scarpe thousands of page every 30 minutes in headless mode from a tor gateway, at best the response time will increase until it become unusable or the IP adress will be blacklisted.

For the kinkiest among you, the script supports authentication to access pages reserved for adults. Multiple factor authentification is supported (if you are not in headless mode).
**If you use the authentication function and play dumb, you risk having your account slowed down, see the number of captcha increase or even get ban**. You've been warned, there's no need to come crying to me afterwards.

I use this script twice a day for about 40 pages and I haven't had any problems for the moment.

## Use

Scrap on specific event page: 
`python3 events-scraper.py -e https://www.facebook.com/somepage/events/ `

Scrap all the page listed inside a file: 
`python3 events-scarper.py -f event_velo.txt `

Scrap all the page listed inside a file and login with the credential inside credential.txt: 
`python3 events-scraper.py -f event_velo.txt -c`

```usage: events-scraper.py [-h] [-e EVENTS [EVENTS ...]] [-c] [-f FILE] [-r RELATED] [-q]

Non API Facebook event miner

optional arguments:
  -h, --help            show this help message and exit
  -e EVENTS [EVENTS ...], --events EVENTS [EVENTS ...]
                        List the pages you want to scrape for events
  -c, --credentials     use credentials in credentials.txt
  -f FILE, --file FILE  File with a list of FB events pages
  -q, --quiet           silence output
```

## Requirements

  * Selenium 
  * icalandar


## ToDo / Know issues

  * Tickets url isn't scrapped
  * Recurrent events and day saving time were not tested
  * Need an argument to specify the ical output filename
  * URL inside the description of the events are removed for no reason 
  * need a headless option
  * need a crash or layout change alert system
  * Credential option work only with the classic layout and don't detect the new FB layout
