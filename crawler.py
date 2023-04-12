
# Written by James Rogers (542046)

import queue
import random
import soundcloud
import time

# ============================================================================ #

CLIENT_ID = <INSERT SOUNDCLOUD API KEY HERE>
STARTING_ID = <INSERT SOUNDCLOUD USER ID HERE>

MINIMUM_FOLLOWERS = 1000000

ADD_PAUSES_BETWEEN_CALLS = True
PAUSE_BETWEEN_USERS_TIME_RANGE = (1, 3)
PAUSE_BETWEEN_RELATIONSHIP_CALLS_TIME_RANGE = (0.1, 1)

ADD_REGULAR_PAUSES = True
REGULAR_PAUSE_FREQUENCY = 100
REGULAR_PAUSE_TIME_RANGE = (60, 180)

# ============================================================================ #

def buildUserAttributesString(user):
    userAttributes = [
        xstr(user.id),
        xstr(user.username),
        xstr(user.country),
        xstr(user.city),
        xstr(user.followers_count),
        xstr(user.followings_count),
        xstr(user.playlist_count),
        xstr(user.reposts_count),
        xstr(user.track_count)
    ]
    return '\t'.join(userAttributes) + '\n'

def buildUserFollowingsString(userId, followings):
    if followings == []:
        return xstr(userId) + '\n'
    else:
        userFollowings = [xstr(followedUser.id) for followedUser in followings]
        return xstr(userId) + '\t' + '\t'.join(userFollowings) + '\n'

def xstr(s):
    if s is None:
        return ''
    else:
        return str(s)

# ============================================================================ #

def filterFollowings(user):
    return user.followers_count >= MINIMUM_FOLLOWERS

def getUserFollowings(client, id):
    followings = getUserRelationships(client, '/users/' + str(id) + '/followings')
    filteredFollowings = list(filter(filterFollowings, followings))
    return filteredFollowings

# A pair of functions that will fetch from SoundCloud a list of user
# relationships for a given href
# - Will pause and retry if the API call fails or the response is malformed
# - Behaves recursively as the API only returns a subset of the relationships
#   for any one API call with the remainder to be fetched at the returned
#   next_href
def getUserRelationships(client, href):
    while True:
        try:
            relationships = client.get(href, page_size = 200)
            collection = list(relationships.collection)
            nextHref = relationships.next_href
            return collection + getUserRelationshipsRecursive(client, nextHref)
        except:
            time.sleep(30)
            continue

def getUserRelationshipsRecursive(client, href):
    if href is None:
        return []

    if ADD_PAUSES_BETWEEN_CALLS:
        time.sleep(random.uniform(*PAUSE_BETWEEN_RELATIONSHIP_CALLS_TIME_RANGE))

    while True:
        try:
            relationships = client.get(href.replace('https://api.soundcloud.com', ''))
            collection = list(relationships.collection)
            nextHref = relationships.next_href
            return collection + getUserRelationshipsRecursive(client, nextHref)
        except:
            time.sleep(30)
            continue

# ============================================================================ #

# A function that takes a list of users, and for each user (providing it has not
# been discovered previously) will add it to the usersToVisit queue, the
# discoveredUsers set, the noFollowings set if relevant, and will write its
# attributes data to the given attributes file
def handleFollowings(followedUsers, discoveredUsers, usersToVisit, noFollowings, attributesFile):
    for user in followedUsers:
        userId = user.id
        if userId not in discoveredUsers:
            attributesFile.write(buildUserAttributesString(user))
            usersToVisit.put((-user.followers_count, userId))
            discoveredUsers.add(userId)
            if user.followings_count == 0:
                noFollowings.add(userId)

# A function that calculates and displays info regarding the crawl's progress
def printCompletionData(count, userId, queueSize, userFollowingsCount, startTime):
    completed = count / (count + queueSize)
    averageTime = (time.time() - startTime) / (count + 1)
    print(
        '{}. {:>9} {:>10,} followers ({} to go / {:.1%} completed / {:.1f}s avg)'
            .format(count, userId, userFollowingsCount, queueSize, completed, averageTime)
    )

# ============================================================================ #

# Set up the SoundCloud client
client = soundcloud.Client(client_id = CLIENT_ID)

# Build a priority queue which will hold all users that have been discovered but
# not yet visited, ordered by the follower count for each user
usersToVisit = queue.PriorityQueue()

# Build a set to keep track of users that have been discovered already
discoveredUsers = set()

# Build a set to keep track of users that don't follow anyone
noFollowings = set()

# Create a file to store the collected user attributes
attributesFile = open('userAttributes.txt', 'w', encoding='utf-8')

# Create a file to store the collected user followings
followingsFile = open('userFollowings.txt', 'w')

count = 0
startTime = time.time()

# Using a starting user id, find its followings to populate the queue
followings = getUserFollowings(client, STARTING_ID)
handleFollowings(followings, discoveredUsers, usersToVisit, noFollowings, attributesFile)
printCompletionData(0, STARTING_ID, usersToVisit.qsize(), 0, startTime)

# While the queue of users is non empty, continue to crawl
continueFor = REGULAR_PAUSE_FREQUENCY
while (not usersToVisit.empty()):
    count += 1

    # Take the user from the queue with the highest follower count
    userFollowersCount, userId = usersToVisit.get()
    userFollowersCount = -userFollowersCount

    # Only make an API call if the user actually follows anyone
    if userId in noFollowings:
        followings = []
    else:
        if ADD_PAUSES_BETWEEN_CALLS:
            time.sleep(random.uniform(*PAUSE_BETWEEN_USERS_TIME_RANGE))
        followings = getUserFollowings(client, userId)

    # Write the user and all of the users it follows to the user followings file
    followingsFile.write(buildUserFollowingsString(userId, followings))

    # Handle the retrieved list of followings
    handleFollowings(followings, discoveredUsers, usersToVisit, noFollowings, attributesFile)

    # Print a summary of the crawl completion at this point
    printCompletionData(count, userId, usersToVisit.qsize(), userFollowersCount, startTime)

    # To avoid a constant stream of requests to SoundCloud that may incur
    # penalties, a regular pause can be actioned by the crawler
    if ADD_REGULAR_PAUSES:
        continueFor -= 1
        if continueFor == 0:
            continueFor = REGULAR_PAUSE_FREQUENCY

            waitTime = random.uniform(*REGULAR_PAUSE_TIME_RANGE)
            print('Waiting for', round(waitTime), 'seconds...')
            time.sleep(waitTime)

# Close the data files now that crawling has completed
attributesFile.close()
followingsFile.close()
