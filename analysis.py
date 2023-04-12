
# Written by James Rogers (542046)

import json
import location
import math
import networkx
import networkx.algorithms.community as community
import operator

# ============================================================================ #

MINIMUM_FOLLOWERS = 200000
MAXIMUM_FOLLOWERS = 10000000

MINIMUM_NUMBER_OF_RELATIONSHIPS = 3
MAXIMUM_NUMBER_OF_RELATIONSHIPS = 100

COMPLETE_ADDITIONAL_GRAPH_ANALYSIS = True

# ============================================================================ #

MALFORMED_USER_LINES = ['10884', '307869']

K_CLIQUE_COMMUNITIES_K_VALUE = 5
COMMUNITY_SIZE_THRESHOLD = 20

# ============================================================================ #

# A function that filters and removes users from the users dictionary by
# removing all relationships that are not bidirectional and then any users that
# do not meet a minimum number of relationships
def filterUsers(users):

    # Repeat the process until no more changes occur
    changed = True
    while changed:
        changed = False

        print('Determine skippable nodes and edges')

        # Create a set to keep track of users that should be deleted later
        skipList = set()

        # For each user, remove any edges that are one-way relationships
        for (userId, user) in users.items():
            incomingEdges = user['followers']
            outgoingEdges = user['following']

            # Only keep user relationships that exist in both directions
            outgoingEdges.intersection_update(incomingEdges)
            incomingEdges.intersection_update(outgoingEdges)

            # If edges are now less than the minimum, add to the skip list
            if len(outgoingEdges) < MINIMUM_NUMBER_OF_RELATIONSHIPS:
                skipList.add(userId)

        # For each user, remove any edges directed to users in the skip list
        for (userId, user) in users.items():
            incomingEdges = user['followers']
            outgoingEdges = user['following']

            # Remove any user relationships that are in the skip list
            outgoingEdges.difference_update(skipList)
            incomingEdges.difference_update(skipList)

        # Remove all users that exist in the skip list from the users dictionary
        for userId in skipList:
            del users[userId]
            changed = True

        print('COMPLETE -', len(users), 'users remaining')

# ============================================================================ #

# A function that converts the given users object to a json object containing
# nodes and links that will be used by the visualisation tool
def writeToJsonFile(jsonFile, users):

    object = {
        'nodes': list(),
        'links': list()
    }

    for (userId, user) in users.items():
        object['nodes'].append({
            'id': userId,
            'name': user['name'].replace('"', ''),
            'color1': user['colour1'],
            'color2': user['colour2'],
            'size': user['followerCount']
        })

    for (sourceUserId, sourceUser) in users.items():
        outgoingEdges = sourceUser['following']
        for targetUserId in outgoingEdges:
            object['links'].append({
                'source': sourceUserId,
                'target': targetUserId
            })

    json.dump(object, jsonFile, indent='\t')

# ============================================================================ #

# A function to find and ouput each user's clique number and degree
def findUserSummaryData(outputFile, graph):
    cliqueNumbers = networkx.node_clique_number(graph)
    degrees = graph.degree(graph)

    for (userId, degree) in degrees:
        outputFile.write(users[userId]['name'] + '\t' + str(degree) + '\t' + str(cliqueNumbers[userId]) + '\n')

# A function to find and ouput generated K-Clique Communities
def findCliqueCommunities(outputFile, graph):
    cliqueCommunities = community.k_clique_communities(graph, K_CLIQUE_COMMUNITIES_K_VALUE)

    count = 0
    for cliqueCommunity in cliqueCommunities:
        count += 1
        outputFile.write('Clique ' + str(count) + ':\n')
        for id in cliqueCommunity:
            outputFile.write(users[id]['name'] + '\n')
        outputFile.write('\n')

# A function to find and ouput communities by continually applying the Girvan
# Newman Partitioning algorithm and listing the each step
def findGirvanNewmanCommunities(outputFile, graph):
    girvanNewmanGenerator = community.girvan_newman(graph)

    count = 0
    for step in girvanNewmanGenerator:
        count += 1
        outputFile.write('Step ' + str(count) + ':\n')

        singles = 0
        doubles = 0
        triples = 0

        shouldQuit = True
        for partition in step:
            names = list(map(lambda id: users[id]['name'], partition))
            outputFile.write(' // '.join(names) + '\n')

            if len(partition) > COMMUNITY_SIZE_THRESHOLD:
                shouldQuit = False
            elif len(partition) == 1:
                singles += 1
            elif len(partition) == 2:
                doubles += 1
            elif len(partition) == 3:
                triples += 1

        outputFile.write('including ' + str(singles) + ' singles\n')
        outputFile.write('including ' + str(doubles) + ' doubles\n')
        outputFile.write('including ' + str(triples) + ' triples\n')
        outputFile.write('\n')

        if shouldQuit:
            break

# A function that recursively bisects a given graph using the Kernighan Lin
# Bisection algorithm, until communities are below a certain size threshold
def doBisectionRecursive(graph):
    if len(graph) <= COMMUNITY_SIZE_THRESHOLD:
        result = [set(map(lambda id: int(id), graph))]
        return result
    else:
        (partitionA, partitionB) = community.kernighan_lin_bisection(graph)
        result = doBisectionRecursive(graph.subgraph(partitionA)) + doBisectionRecursive(graph.subgraph(partitionB))
        return result

# A function to find and ouput communities by recursively applying the Kernighan
# Lin Bisection algorithm and listing the final results
def findKernighanLinCommunities(outputFile, graph):
    bisectionCommunities = doBisectionRecursive(graph)

    count = 0
    for bisectionCommunity in bisectionCommunities:
        count += 1
        outputFile.write('Partition ' + str(count) + ':\n')
        names = list(map(lambda id: users[str(id)]['name'], bisectionCommunity))
        outputFile.write(' // '.join(names) + '\n')
        outputFile.write('\n')

# ============================================================================ #

# Create a dictionary of users
users = {}

# Open the scraped data files
attributesFile = open('userAttributes.txt', 'r', encoding='utf-8')
followingsFile = open('userFollowings.txt', 'r')

attributesFileLines = list(attributesFile)
followingsFileLines = list(followingsFile)

attributesFile.close()
followingsFile.close()

# Create a list to keep track of user locations
userLocations = []

# Parse the User Attributes file and start building the users dictionary
print('Parsing the Attributes file -', len(attributesFileLines), 'lines')

for line in attributesFileLines:
    # Parse the line
    splitLine = line.replace('\n', '').split('\t')
    userId, userName, userCountry, userCity, userFollowerCount, *_ = splitLine

    # Some lines from the collected data are malformed due to use of special
    # characters, so ignore these for the purposes of the analysis
    if userId not in MALFORMED_USER_LINES:

        # Only take users that are within the minimum and maximum follower count
        if int(userFollowerCount) >= MINIMUM_FOLLOWERS and int(userFollowerCount) <= MAXIMUM_FOLLOWERS:

            # Determine the location name and colours for this location
            userLocation = location.getLocationName(userCountry, userCity)
            userLocations.append(userLocation)
            userLocationColours = location.getLocationColours(userLocation)

            # Add the user and its metadata to the users dictionary, including
            # empty sets to keep track of followers and following relationships
            users[userId] = {
                'name': userName,
                'followers': set(),
                'following': set(),
                'colour1': userLocationColours[0],
                'colour2': userLocationColours[1],
                'followerCount': userFollowerCount
            }

print('COMPLETE -', len(users), 'users')
print()

# Analyse the user locations and display a summary
print('Analysing the user locations')
location.analyseLocations(userLocations)
print()

# Parse the User Followings file and continue to build the users dictionary
print('Parsing the Followings file -', len(followingsFileLines), 'lines')
for line in followingsFileLines:
    # Parse the line
    splitLine = line.replace('\n', '').split('\t')
    sourceUserId, *targetUsers = splitLine

    # For every user that this source user follows, add the relationship to both
    # this source user's following set, and the target user's followers set
    for targetUserId in targetUsers:
        if targetUserId != '' and sourceUserId in users and targetUserId in users:
            users[sourceUserId]['following'].add(targetUserId)
            users[targetUserId]['followers'].add(sourceUserId)

print('COMPLETE -', len(users), 'users')
print()

# ============================================================================ #

# Filter the users to only those with a minimum number of bidirectional edges
filterUsers(users)

# Also filter out any users with too many relationships
print('Remove users with more than', MAXIMUM_NUMBER_OF_RELATIONSHIPS, 'current relationships')

skipList = set()

# If a user has too many relationships, add it to the skip list
for (userId, user) in users.items():
    if len(user['followers']) >= MAXIMUM_NUMBER_OF_RELATIONSHIPS:
        skipList.add(userId)

# For each user, remove any edges directed to users in the skip list
for (userId, user) in users.items():
    user['following'].difference_update(skipList)
    user['followers'].difference_update(skipList)

# Remove all users that exist in the skip list from the users dictionary
for userId in skipList:
    del users[userId]

print('COMPLETE -', len(users), 'users remaining')

# Now that users with too many relationships have been removed, filter again
filterUsers(users)
print()

# ============================================================================ #

# Export an object containing nodes and links to be used by the visualiation
# tool to followings.json
print('Write to followings.json')
followingsOutputFile = open('followings.json', 'w', encoding='utf-8')
writeToJsonFile(followingsOutputFile, users)
followingsOutputFile.close()
print('COMPLETE')
print()

# ============================================================================ #

if COMPLETE_ADDITIONAL_GRAPH_ANALYSIS:

    # Create a NetworkX graph object
    graph = networkx.Graph()

    # Build the in-memory NetworkX graph object by adding nodes and edges
    print('Build the graph object')
    for (sourceUserId, sourceUser) in users.items():
        graph.add_node(sourceUserId)

        outgoingEdges = sourceUser['following']
        for targetUserId in outgoingEdges:
            graph.add_edge(sourceUserId, targetUserId)

    # Use only the main connected component of the graph for the analysis
    largestConnectedComponent = max(networkx.connected_components(graph), key=len)
    graph = graph.subgraph(largestConnectedComponent)
    print('COMPLETE')

    # Export a list of user summary data including the degree and clique number for each user
    print('Finding the degree and clique number for each user')
    userSummaryOutputFile = open('user_summary.txt', 'w', encoding='utf-8')
    findUserSummaryData(userSummaryOutputFile, graph)
    userSummaryOutputFile.close()
    print('COMPLETE')

    # Export a list of communities found using the K-Clique Communities method
    print('Finding communities using the K-Clique Communities method')
    cliqueCommunitiesOutputFile = open('clique_communities.txt', 'w', encoding='utf-8')
    findCliqueCommunities(cliqueCommunitiesOutputFile, graph)
    cliqueCommunitiesOutputFile.close()
    print('COMPLETE')

    # Export a list of communities found using the Girvan Newman Partitioning algorithm
    print('Finding communities using the Girvan Newman Partitioning algorithm')
    girvanNewmanOutputFile = open('girvan_newman.txt', 'w', encoding='utf-8')
    findGirvanNewmanCommunities(girvanNewmanOutputFile, graph)
    girvanNewmanOutputFile.close()
    print('COMPLETE')

    # Export a list of communities found using the Kernighan Lin Bisection algorithm
    print('Finding communities using the Kernighan Lin Bisection algorithm')
    kernighanLinOutputFile = open('kernighan_lin.txt', 'w', encoding='utf-8')
    findKernighanLinCommunities(kernighanLinOutputFile, graph)
    kernighanLinOutputFile.close()
    print('COMPLETE')
