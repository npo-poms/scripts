import shelve
import urllib2
import sys
import base64
from xml.dom import minidom
from pprint import pprint
import getopt
import getpass

target='https://api-test.poms.omroep.nl/'
"""The currently configured target. I.e. the URL of the POMS rest api"""



def init(opts = None):
    """username/password and target are stored in a database.
    If no username/password is known for a target, it is asked"""

    global target
    global _opts
    _opts = [] if opts is None else opts
    d = shelve.open('creds.db')

    if not 'target' in d:
        d['target'] = target

    for o,a in opts:
        if o == '-t':
            if a == 'test':
                a = 'https://api-test.poms.omroep.nl/'
            if a == 'dev':
                a = 'https://api-dev.poms.omroep.nl/'
            if a == 'prod':
                a = 'https://api.poms.omroep.nl/'
            if a == 'localhost':
                a = 'http://localhost:8071/rs/'
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

def opts(args = "t:e:srh", usage = None, minargs = 0):
    try:
        opts, args = getopt.getopt(sys.argv[1:], args)
    except getopt.GetoptError as err:
        print(err)
        if usage is not None:
            usage()
        generic_usage();
        sys.exit(2)

    for o, a in opts:
        if o == '-h':
            if usage is not None:
                usage()
            generic_usage()
            sys.exit(0)
        del sys.argv[0]
    if len(args) < minargs:
        if usage is not None:
            usage()
        generic_usage()
        sys.exit(1)

    init(opts)
    return opts,args

def _creds(pref = ""):
    d = shelve.open('creds.db')
    usernamekey = pref + d['target'] + ':username'
    passwordkey = pref + d['target'] + ':password'

    if not usernamekey in d  or ('-r','') in _opts :
        d[usernamekey] = raw_input('Username for ' + target + ': ')
        d[passwordkey]  = getpass.getpass()
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
    else:
        email = None
    d.close()

def generic_usage():
    print "-s       Show stored credentials (in creds.db). If none stored, username/password " + \
        "will be asked interactively."
    print "-t <url> Change target. 'test', 'dev' and 'prod' are " + \
          "possible abbreviations for https://api[-test|-dev].poms.omroep.nl/media/. " + \
          "Defaults to previously used version (stored in creds.db)"
    print "-r       Reset and ask username/password again"
    print "-e <email> Set email address to mail errors to. " + \
          "Defaults to previously used value (stored in creds.db)."

def _members_or_episodes(mid, what):
    _creds()
    print "loading members of " + mid
    result = []
    offset = 0
    batch = 20
    while True:
        url = (target + 'media/group/' + mid + "/" + what + "?max=" + str(batch) +
               "&offset=" + str(offset))
        xml = _get_xml(url)
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
    """return a list of all members of a group. As XML objects, wrapped
    in 'items', do you can see the position"""
    return _members_or_episodes(mid, "members")

def episodes(mid):
    """return a list of all episodes of a group. As XML objects, wrapped
    in 'items', do you can see the position"""
    return _members_or_episodes(mid, "episodes")

def get_memberOf_xml(groupMid, position=0, highlighted="false"):
    return ('<memberOf position="' + str(position) + '" highlighted="' +
            highlighted + '">' + groupMid + '</memberOf>')

def add_member(groupMid, memberMid, position=0, highlighted="false"):
    url = target + "api/media/" + memberMid + "/memberOf"
    xml = getMemberOfXml(groupMid, position, highlighted)
    response = urllib2.urlopen(urllib2.Post(url, data=xml))

def post_str(xml):
    return post(minidom.parseString(xml).documentElement)

def parkpost_str(xml):
    return parkpost(minidom.parseString(xml).documentElement)


def get(mid):
    _creds()
    url = target + "media/media/" + mid
    return _get_xml(url)


def _get_xml(url):
    try:
        response = urllib2.urlopen(urllib2.Request(url))
    except Exception as e:
        print url + " " + str(e)
        sys.exit(1)

    xmlStr = response.read();
    try:
        xml = minidom.parseString(xmlStr)
    except Exception as e:
        print "Could not parse \n" + xmlStr
    return xml



def add_genre(xml, genreId):
    """Adds a genre to the minidom object"""

    genreEl = xml.ownerDocument.createElement("genre")
    genreEl.appendChild(xml.ownerDocument.createTextNode(genreId))
    _append_element(xml, genreEl)


def _append_element(xml, element, path = ("crid",
                                          "broadcaster",
                                          "portal",
                                          "exclusive",
                                          "region",
                                          "title",
                                          "description",
                                          "tag",
                                          "genre",
                                          "avAttributes",
                                          "releaseYear",
                                          "duration",
                                          "credits",
                                          "memberOf",
                                          "ageRating",
                                          "contentRating",
                                          "email",
                                          "website",
                                          "location",
                                          "scheduleEvents",
                                          "relation",
                                          "images",
                                          "asset")):
    """Appends an element in the correct location in the given (minidom) xml"""
    index =  path.index(element.nodeName)
    for child in xml.childNodes:
        if path.index(child.nodeName) > index:
            xml.insertBefore(element, child)
            return
    xml.appendChild(element)


def post(xml, lookupcrid=False):
    _creds()
    # it seems minidom sucks a bit, since it should have added these attributes
    # automaticly of course. The xml is simply not valid otherwise
    xml.setAttribute("xmlns", "urn:vpro:media:update:2009")
    xml.setAttribute("xmlns:xsi",
                     "http://www.w3.org/2001/XMLSchema-instance")
    url = target + "media/media?lookupcrid=" + str(lookupcrid)

    if email:
        url += "&errors=" + email


    #print xml.toxml()
    print "posting " + xml.getAttribute("mid") + " to " + url
    req = urllib2.Request(url, data=xml.toxml('utf-8'))
    return _post(xml, req)



def parkpost(xml):
    _creds("parkpost:")
    url = target + "parkpost/promo"

    print "posting to " + url
    req = urllib2.Request(url, data=xml.toxml('utf-8'))
    return _post(xml, req)


def _post(xml, req):
    req.add_header("Authorization", authorizationHeader);
    req.add_header("Content-Type", "application/xml")
    req.add_header("Accept", "text/plain")
    #req.add_header("Accept", "application/json")
    try:
        response = urllib2.urlopen(req)
        return response.read()
    except urllib2.HTTPError as e:
        error_message = e.read()
        print error_message
        return None
