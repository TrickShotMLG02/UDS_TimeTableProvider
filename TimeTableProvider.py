from collections import namedtuple
from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime
from pathlib import Path
import os
import pytz
import requests
import re

Pair = namedtuple("Pair", ["first", "second"])
WEEKDAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# THIS CLASS IS USED FOR REPRESENTING ASSIGNED TUTORIALS
class Tutorial:
    def __init__(self, id, time, day):
        self.tutorialId = id
        self.tutorialTime = time
        self.tutorialDay = day

    # This function checks whether a specific entry matches the current tutorial
    def equals(self, calEntry):
        entryId = calEntry.getTutorialId()
        entryTime = calEntry.getTutorialTime()
        entryDay = calEntry.getTutorialDay()
        if entryId == -1:
            return entryTime == self.tutorialTime and entryDay == self.tutorialDay
        else:
            return entryId == self.tutorialId and entryTime == self.tutorialTime and entryDay == self.tutorialDay

    # This function checks if a calendar contains a tutorial
    def containsTutorial(self, cal):
        for entry in cal:
            if self.equals(entry):
                return True
        return False


### CONFIGURATION SECTION START ###

# PATH TO THE FINAL CALENDAR FILE
calendarPath = "/media/Media/Downloads/Calendars/"
calendarName = "Semester2324.ics"

# ONE VARIABLE FOR EACH TIMETABLE THAT SHOULD BE USED WITH THE CORRESPONDING URL
algodat = "https://cms.sic.saarland/gzad2324/termine/events/download/prefix:1"
ti = "https://cms.sic.saarland/ti2324/termine/events/download/prefix:1"
mfi3 = "https://cms.sic.saarland/mfcs3_wise2324/termine/events/download/prefix:1"
mfi1 = "https://cms.sic.saarland/mfi1_mfcs1_wise2324/termine/events/download/prefix:1"
prog1 = "https://cms.sic.saarland/prog1_23/termine/events/download/prefix:1"
eml = "https://cms.cispa.saarland/eml23/termine/events/download/prefix:1"

# ONE VARIABLE FOR EACH TUTORIAL THAT WAS ASSIGNED IN CMS
algodatTut = Tutorial(1, "10:00", "Monday")
tiTut = Tutorial(3, "12:15", "Tuesday")
mfi3Tut = Tutorial(7, "10:15", "Thursday")
mfi1Tut = Tutorial(16, "14:00", "Thursday")
prog1Tut = Tutorial(17, "12:00", "Wednesday")
emlTut = Tutorial(9, "12:00", "Monday")

# LIST OF ALL TIMETABLES THAT SHOULD BE CONSIDERED
calUrls = [
    Pair(algodat, algodatTut),
    Pair(ti, tiTut),
    Pair(mfi3, mfi3Tut),
    Pair(mfi1, mfi1Tut),
    Pair(prog1, prog1Tut),
    Pair(eml, emlTut)
]


### CONFIGURATION SECTION END ###


# DOWNLOAD ALL CALENDARS FROM THE GIVEN URLS
def downloadCalendars(calendarURLs):
    cals = []
    for entry in calendarURLs:
        # get url
        url = entry.first

        # download the calendar and check if it was successful
        req = requests.get(url)
        if req.status_code != 200:
            print("Error {} fetching {}: {}"
                  .format(url, req.status_code, req.text))
            continue

        # parse the calendar
        cal = Calendar.from_ical(req.text)

        # add calendar with assigned tutorial to list
        cals.append(Pair(cal, entry.second))

    # return calendars list
    return cals


# REMOVE ALL MATCHING ENTRIES FROM A CALENDAR
def removeTutorials(cal: Calendar, assignedTutorial: Tutorial):
    # Define the criteria for removal
    remove_criteria = {
        'isTutorial': "Tutorial",  # Entries with "Tutorial" in summary
        'tutorialId': assignedTutorial.tutorialId,  # Entries without the ID in summary
        'tutorialDay': assignedTutorial.tutorialDay,  # Specific day
        'tutorialTime': assignedTutorial.tutorialTime,  # Specific time
    }

    # Iterate through the events and filter based on criteria
    events_to_remove = []
    for component in cal.walk():
        # Check if the component is an event
        if component.name == "VEVENT":

            try:
                eventSummary = component.get('summary')
                eventDay = WEEKDAYS[component.get('dtstart').dt.weekday()]
                eventTimeStamp = component.get('dtstart').dt.astimezone(pytz.timezone('Europe/Berlin'))
                eventTime = eventTimeStamp.strftime('%H:%M')

                if remove_criteria['isTutorial'] in eventSummary:
                    tutId = int(remove_criteria['tutorialId'])

                    # Define the regular expression pattern to match the tutorial id after the first colon
                    pattern = fr':[^:]*{tutId}'

                    # Search for the pattern in the string
                    if tutId != -1 and re.search(pattern, eventSummary):
                        # Do nothing
                        pass
                    elif eventDay == remove_criteria['tutorialDay'] and eventTime == remove_criteria['tutorialTime']:
                        # Do nothing
                        pass
                    else:
                        # Add to list of events to remove
                        events_to_remove += [component]
            except:
                pass

    # Remove the filtered events from the components in calendar
    for event in events_to_remove:
        cal.subcomponents.remove(event)

    return cal


# ADD ALL ENTRIES TO A CALENDAR
def addEntriesToCalendar(cal, entries):
    return -3


# MERGE ALL CALENDARS INTO ONE FILE
def mergeCalendars(cals):
    merged_calendar = Calendar()

    for cal in cals:
        for component in cal.walk():
            merged_calendar.add_component(component)

    return merged_calendar


# UPDATE THE CALENDAR FILE ON DISK
def updateCalendarFile(cal: Calendar):
    # Write to current working directory
    directory = Path.cwd() / 'MyCalendar'

    # Write to a specific directory
    directory = calendarPath
    try:
        directory.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("Folder already exists")
    else:
        print("Folder was created")

    f = open(os.path.join(directory, calendarName), 'wb')
    f.write(cal.to_ical())
    f.close()


def main():
    # DOWNLOAD ALL CALENDARS
    cals = downloadCalendars(calUrls)
    newCals = []

    for calEntry in cals:
        # REMOVE ALL MATCHING ENTRIES FROM A CALENDAR
        cal = calEntry.first
        tut = calEntry.second
        cal = removeTutorials(cal, tut)
        newCals.append(cal)

        # ADD ALL ENTRIES TO A CALENDAR
        # addEntriesToCalendar(cal, entries)

        # MERGE ALL CALENDARS INTO ONE FILE
        newCal = mergeCalendars(newCals)

        # UPDATE THE LOCAL CALENDAR FILE
        updateCalendarFile(newCal)


if __name__ == "__main__":
    main()
