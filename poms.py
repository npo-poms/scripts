import shelve
import urllib2
import sys
import base64
from xml.dom import minidom
from pprint import pprint


target='https://api-test.poms.omroep.nl/media/'
"""The currently configured target. I.e. the URL of the POMS rest api"""



def init(opts = []):
    """username/password and target are stored in a database. If no username/password is known for a target, it is asked"""

    global target
    global _opts
    _opts = opts
    d = shelve.open('creds.db')

    if not 'target' in d:
        d['target'] = target

    for o,a in opts:
        if o == '-t':
            if a == 'test':
                a = 'https://api-test.poms.omroep.nl/media/'
            if a == 'dev':
                a = 'https://api-dev.poms.omroep.nl/media/'
            if a == 'prod':
                a = 'https://api.poms.omroep.nl/media/'
            if a == 'localhost':
                a = 'http://localhost:8071/rs/media/'
            if a != d['target']:
                print "Setting target to " + a
                d['target'] = a
        if o == '-e':
            d['email'] = a

        if o == '-s':
            for k in d.keys():
                print k + "=" + d[k]


    target=d['target']
    d.close()

def _creds():
    d = shelve.open('creds.db')
    usernamekey = d['target'] + ':username'
    passwordkey = d['target'] + ':password'

    if not usernamekey in d  or ('-r','') in _opts :
        d[usernamekey] = raw_input('Username for ' + target + ': ')
        d[passwordkey]  = raw_input('Password: ')
        print "Username/password stored in file creds.db. Use -r to set it."


    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, target, d[usernamekey], d[passwordkey])
    urllib2.install_opener(urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman)))

    global authorizationHeader
    base64string = base64.encodestring('%s:%s' % (d[usernamekey], d[passwordkey]))[:-1]
    authorizationHeader = "Basic %s" % base64string
    global email
    if 'email' in d:
        email = d['email']

    d.close()

def usage():
    print "-s       show stored credentials"
    print "-t <url> change target. 'test', 'dev' and 'prod' are possible abbreviations for https://api[-test|-dev].poms.omroep.nl/media/"
    print "-r       reset and ask username/password again"
    print "-e <email> sets email-adress to mail errors to"

def _membersOrEpisodes(mid, what):
    _creds()
    print "loading members of " + mid
    result = []
    offset = 0
    batch = 20
    while True:
        url = target + 'group/' + mid + "/" + what + "?max=" + str(batch) + "&offset=" + str(offset)
        response = urllib2.urlopen(urllib2.Request(url))
        xml = minidom.parseString(response.read())

        items = xml.getElementsByTagName('item')
        result.extend(items)
        if len(items) == 0:
            break
        offset += batch
        #print xml.childNodes[0].toxml('utf-8')
        total = xml.childNodes[0].getAttribute("totalCount")
        print str(len(result)) + "/" + total


    return result


def members(mid):
    """return a list of all members of a group. As XML objects, wrapped in 'items', do you can see the position"""
    return _membersOrEpisodes(mid, "members")

def episodes(mid):
    """return a list of all episodes of a group. As XML objects, wrapped in 'items', do you can see the position"""
    return _membersOrEpisodes(mid, "episodes")

def getMemberOfXml(groupMid, position=0, highlighted="false"):
    return '<memberOf position="' + str(position) + '" highlighted="' + highlighted + '">' + groupMid + '</memberOf>'

def addMember(groupMid, memberMid, position=0, highlighted="false"):
    url = target + "media/" + memberMid + "/memberOf"
    xml = getMemberOfXml(groupMid, position, highlighted)
    response = urllib2.urlopen(urllib2.Post(url, data=xml))

def post(xml):
    # it seems minidoc sucks a bit, since it should have added these attributes automaticly of course. The xml is simply not valid otherwise
    xml.setAttribute("xmlns", "urn:vpro:media:update:2009")
    xml.setAttribute("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")
    url = target + "media?errors=" + email
    print "posting " + xml.getAttribute("mid") + " to " + url
    req = urllib2.Request(url, data=xml.toxml('utf-8'))
    req.add_header("Authorization", authorizationHeader);
    req.add_header("Content-Type", "application/xml")
    req.add_header("Accept", "application/json")
    response = urllib2.urlopen(req)
