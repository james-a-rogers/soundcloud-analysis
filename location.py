
# Written by James Rogers (542046)

import operator

# ============================================================================ #

WHITE = '#FFFFFF'
RED = '#CC0000'
RED_LIGHT = '#CC6666'
BLUE = '#0000CC'
BLUE_LIGHT = '#6666CC'
YELLOW = '#FFCC00'
GREEN = '#009900'
GREY = '#999999'
DARK_GREY = '#333333'
ORANGE = '#FF9900'

COUNTRY_COLOURS = {
    'United States': (BLUE_LIGHT, BLUE),
    'United Kingdom': (RED_LIGHT, RED),
    'Germany': (RED, DARK_GREY),
    'Netherlands': (ORANGE, BLUE),
    'France': (WHITE, BLUE),
    'Canada': (WHITE, RED),
    'Australia': (GREEN, YELLOW),
    'Brazil': (YELLOW, GREEN),
    'Sweden': (YELLOW, BLUE),
    'Italy': (WHITE, GREEN),
    'Spain': (YELLOW, RED),
    'OTHER': (GREY, GREY),
    'NOT SPECIFIED': (GREY, GREY),
    'NOT DETERMINED': (GREY, GREY)
}

# A function that assigns a node colour for a given location
def getLocationColours(location):
    (country, city) = location
    if country in COUNTRY_COLOURS:
        return COUNTRY_COLOURS[country]
    else:
        return COUNTRY_COLOURS['OTHER']

# ============================================================================ #

# A function that attempts to determine a location from a given country/city pair
def getLocationName(country, city):

    city = city.lower().strip()

    # Capture all common cases of where there is no clear location specified
    if country == '' and city in ['', 'worldwide', 'world']:
        return ('NOT SPECIFIED', '')

    # Capture all common cases of popular cities
    elif city == 'london':
        return ('United Kingdom', 'London')
    elif city in ['los angeles', 'los angeles, ca', 'la']:
        return ('United States', 'Los Angeles')
    elif city == 'berlin':
        return ('Germany', 'Berlin')
    elif city in ['new york', 'new york city', 'nyc']:
        return ('United States', 'New York')
    elif city == 'paris':
        return ('France', 'Paris')
    elif city == 'amsterdam':
        return ('Netherlands', 'Amsterdam')
    elif city == 'toronto':
        return ('Canada', 'Toronto')
    elif city == 'chicago':
        return ('United States', 'Chicago')
    elif city == 'stockholm':
        return ('Sweden', 'Stockholm')
    elif city == 'brooklyn':
        return ('United States', 'Brooklyn')
    elif city == 'atlanta':
        return ('United States', 'Atlanta')
    elif city == 'melbourne':
        return ('Australia', 'Melbourne')
    elif city == 'sydney':
        return ('Australia', 'Sydney')
    elif city == 'san francisco':
        return ('United States', 'San Francisco')
    elif city == 'cairo':
        return ('Egypt', 'Cairo')
    elif city == 'miami':
        return ('United States', 'Miami')
    elif city == 'hamburg':
        return ('Germany', 'Hamburg')
    elif city == 'são paulo':
        return ('Brazil', 'São Paulo')
    elif city == 'nashville':
        return ('United States', 'Nashville')

    # Capture all remaining cases of the United Kingdom
    elif country == 'Britain (UK)':
        if city == '':
            return ('United Kingdom', '')
        else:
            return ('United Kingdom', 'OTHERS')

    # Capture all remaining cases of all other countries
    elif country != '':
        if city == '':
            return (country, '')
        else:
            return (country, 'OTHERS')

    # For all other cases that haven't been caught by simple string matching
    else:
        return ('NOT DETERMINED', '')

# ============================================================================ #

# A function to count and print a summary of the most popular locations
def analyseLocations(locations):
    locationCount = 0
    locationCounts = {}
    for location in locations:
        if location != ('NOT SPECIFIED', ''):
            locationCounts[location] = locationCounts.get(location, 0) + 1
            locationCount += 1

    count = 0
    cumulative = 0
    for key, value in sorted(locationCounts.items(), key=operator.itemgetter(1)):
        count += 1
        cumulative += value

        print(
            '{:>3}. {:>15} {:>15}\t{} / {:.2%} / {:.2%}'
                .format(
                    len(locationCounts) - count + 1,
                    key[0],
                    key[1],
                    value,
                    value / locationCount,
                    cumulative / locationCount
                )
        )
