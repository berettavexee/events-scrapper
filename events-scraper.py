#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2020 Guiral Lacotte

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
import os
import sys
import argparse
import re
import json
from datetime import datetime
import pytz
from icalendar import Calendar, Event, vCalAddress, vText
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException  # TimeoutException

BROWSER_EXE = '/usr/bin/firefox'
GECKODRIVER = '/usr/bin/geckodriver'

FIREFOX_BINARY = FirefoxBinary(BROWSER_EXE)

#  Code to disable notifications pop up of Chrome Browser

PROFILE = webdriver.FirefoxProfile()
# PROFILE.DEFAULT_PREFERENCES['frozen']['javascript.enabled'] = False
PROFILE.set_preference("dom.webnotifications.enabled", False)
PROFILE.set_preference("app.update.enabled", False)
PROFILE.update_preferences()


class CollectEvents():
    """
    Collector of FaceBook events.

    """

    def __init__(
            self,
            ids=["oxfess"],
            corpus_file="events.json",
            delay=5):
        self.ids = ids
        self.dump = corpus_file
        self.delay = delay
        # browser instance
        self.browser = webdriver.Firefox(executable_path=GECKODRIVER,
                                         firefox_binary=FIREFOX_BINARY,
                                         firefox_profile=PROFILE,)
        self.events_list = []

    def collect(self):
        """
        Manage the user inputs
        Main method
        """
        for iden in self.ids:
            self.collect_event(iden)

        self.remove_duplicate()
        # self.save_json()
        self.save_ical()
        self.browser.close()

    def collect_event(self, page):
        """
        Scrapping function
        """
        # navigate to page
        self.browser.get(page)
        self.browser.implicitly_wait(self.delay)

        # Following line will timeout if there is no upcoming evenet
        # div id is different in that case (no_upcoming_events_card)
        try:
            WebDriverWait(
                self.browser, self.delay).until(
                EC.presence_of_element_located((By.ID, "upcoming_events_card")))
        except Exception:
            print("Time out on page: {}".format(page))
            return None

        # Once the full page is loaded, we can start scrap links inside
        # upcoming_events_card
        links = self.browser.find_elements_by_xpath(
            "//div[@id='upcoming_events_card']/descendant::a")
        links = [
            link for link in links if "facebook.com/events" in link.get_attribute("href")]
        links = [link.get_attribute("href") for link in links]
        print("{} events found on page".format(len(links)), page)

        # Phase 2 : scrap events informations

        for link in links:
            self.browser.get(link)
            WebDriverWait(
                self.browser, self.delay).until(
                EC.visibility_of_element_located((By.ID, "title_subtitle")))
            event_info = {}
            event_info["summary"] = self.browser.find_element_by_id(
                "seo_h1_tag").text
            event_info["location"] = self.browser.find_element_by_class_name(
                "_4dpf._phw").text
            event_info = self.find_dates(event_info)
            event_info["id"] = link.split("/")[4]
            event_info["url"] = "https://www.facebook.com/events/" + \
                str(event_info["id"])
            event_info["description"] = self.browser.find_element_by_class_name(
                "_63ew").text
            event_info["description"] += "\n\n" + event_info["url"]
            event_info = self.find_organizer(event_info)
            self.events_list.append(event_info)

        return

    def find_dates(self, event_info):
        """
        Retrieve start and end dates
        """
        dates = self.browser.find_element_by_class_name(
            "_2ycp").get_attribute("content").split()
        event_info["start"] = datetime.fromisoformat(dates[0])
        if len(dates) >= 3:
            event_info["end"] = datetime.fromisoformat(dates[2])
        else:
            # If an event have no end, assume it one hour long.
            event_info["end"] = event_info["start"] + \
                datetime.timedelta(hours=1)
        return event_info

    def find_organizer(self, event_info):
        """
        Retrieve the firs organizers
        ToDo: manage multiple organizers
        """
        organizer = self.browser.find_elements_by_xpath(
            "//div[@class='_b9-']/descendant::a")
        event_info["organizer"] = organizer[0].text
        return event_info

    def remove_duplicate(self):
        '''
        Remove duplicat in a list of dict
        input: list of dict
        output: list of dict
        '''
        print("Event before deduplicaiton:", len(self.events_list))
        self.events_list = [
            dict(t) for t in {
                tuple(
                    d.items()) for d in self.events_list}]
        print("Event after deduplicaiton:", len(self.events_list))
        return self.events_list

    def save_json(self):
        """
        Dump the event to JSON
        temporary and mostly for debug prupose
        """
        with open(self.dump, "a+", newline='', encoding="utf-8") as outfile:
            json.dump(
                self.events_list,
                outfile,
                indent=4,
                sort_keys=True,
                default=str)

    def save_ical(self, filename='output.ical'):
        '''
        Save events_list as an ical calandar
        input: self
        output: filename.ical

        most of the code of this method is copy/path from icalandar doc.
        The rest is datetime object and timezone crap.

        '''
        cal = Calendar()
        cal.add('prodid', '-//Crappy Calandar Cow/')
        cal.add('version', '2.0')

        for item in self.events_list:
            event = Event()
            event.add('summary', item["summary"])
            event.add('dtstart', item["start"].astimezone(pytz.utc))
            event.add('dtend', item["end"].astimezone(pytz.utc))
            event.add('dtstamp', datetime.utcnow())
            event.add('location', vText(item["location"]))
            event.add('description', vText(item["description"]))
            event.add('class', 'PUBLIC')
            organizer = vCalAddress('MAILTO:noreply@facebook.com')
            organizer.params['cn'] = vText(item["organizer"])
            event['organizer'] = organizer
            # event['location'] = vText(item["organizer"])
            event['uid'] = item["id"] + '@facebook.com'
            # add the event to calandar
            cal.add_component(event)

        with open(filename, 'wb') as filehandle:
            filehandle.write(cal.to_ical())

    def safe_find_element_by_id(self, elem_id):
        '''
        Find element by ID
        input: elem_id
        return: elemts
        '''
        try:
            return self.browser.find_element_by_id(elem_id)
        except NoSuchElementException:
            return None

    def login(self, email, password):
        '''
        Login into FB
        Note: We bypass the FaceBook-Graph-API by using a
        selenium FireFox instance!
        This is against the FB guide lines and thus not allowed.
        USE THIS FOR EDUCATIONAL PURPOSES ONLY. DO NOT ACTAULLY RUN IT.
        '''
        try:
            self.browser.get("https://www.facebook.com")
            self.browser.maximize_window()

            # filling the form
            self.browser.find_element_by_name('email').send_keys(email)
            self.browser.find_element_by_name('pass').send_keys(password)

            # clicking on login button
            self.browser.find_element_by_id('loginbutton').click()
            # if your account uses multi factor authentication
            mfa_code_input = self.safe_find_element_by_id('approvals_code')

            if mfa_code_input is None:
                return

            mfa_code_input.send_keys(input("Enter MFA code: "))
            self.browser.find_element_by_id('checkpointSubmitButton').click()

            # there are so many screens asking you to verify things. Just skip
            # them all
            while self.safe_find_element_by_id(
                    'checkpointSubmitButton') is not None:
                dont_save_browser_radio = self.safe_find_element_by_id('u_0_3')
                if dont_save_browser_radio is not None:
                    dont_save_browser_radio.click()

                self.browser.find_element_by_id(
                    'checkpointSubmitButton').click()

        except Exception as exception:
            print("There's some error in log in.")
            print(exception)
            print(sys.exc_info()[0])
            sys.exit()


def parse_file(file_path):
    '''
    Parse FB page file
    input: filepath
    output: list of urls

    Retrieve correctly formated events page from the input file.
    Try to prevent crash due to human error.
    '''
    # Check if the file exist
    if not os.path.isfile(file_path):
        sys.exit('No such file or directory: {}'.format(file_path))

    # Open the file
    with open(file_path) as file:
        lines = file.read().splitlines()
    urls = []
    for line in lines:
        # Filters anything that doesn't look like an FB events page url
        if re.match(r'^(https://)?(www.)?facebook.com/\S+/events/$', line):
            urls.append(line)
    if len(urls) <= 0:
        sys.exit('Error no facebook url found in {}'.format(file_path))

    return urls


def get_credentials(file_path='credentials.txt'):
    '''
    Retrieve credentials from credentials.txt
    output: email, password

    '''
    # Check if the file exist
    if not os.path.isfile(file_path):
        sys.exit('No such file or directory: {}'.format(file_path))

    with open(file_path) as file:
        email = file.readline().split('"')[1]
        password = file.readline().split('"')[1]
        if email == "" or password == "":
            print(
                "Your email or password is missing. Kindly write them in credentials.txt")
            sys.exit()
    return(email, password)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Non API public FB event miner')
    parser.add_argument('-e', '--events', nargs='+',
                        dest="events",
                        help="List the pages you want to scrape for events")
    parser.add_argument('-c', '--credentials',
                        action='store_true',
                        help="use credentials in credentials.txt")
    parser.add_argument('-f',
                        '--file',
                        dest='file',
                        help='File with a list of FB pages')
    parser.add_argument('-r',
                        '--related ',
                        dest='related',
                        help='list related pages')
    parser.add_argument('-q',
                        '--quiet',
                        action='store_true',
                        help='silence output')
    args = parser.parse_args()
    # Quiet mode
    if args.quiet:
        sys.stdout = sys.stderr = open(os.devnull, 'w')

    events_url = []
    if args.events:
        events_url = events_url + args.events
    if args.file:
        events_url = events_url + parse_file(args.file)
    if len(events_url) == 0:
        sys.exit('No input provided')

    C = CollectEvents(ids=events_url)
    if args.credentials:
        login, password = get_credentials()
        C.login(login, password)
    C.collect()
