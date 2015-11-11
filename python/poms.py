import shelve
import urllib.request
import sys
import base64
import xml.etree.ElementTree as ET
from xml.dom import minidom
import getopt
import getpass
import os
import logging
import pytz
import subprocess
import threading

environments = {
    'test': 'https://api-test.poms.omroep.nl/',
    'dev' : 'https://api-dev.poms.omroep.nl/',
    'prod' : 'https://api.poms.omroep.nl/',
    'localhost': 'http://localhost:8071/rs/'
}

target = None
"""The currently configured target. I.e. the URL of the POMS rest api"""

email = None

authorizationHeader = None

namespaces = {'update': 'urn:vpro:media:update:2009'}


def init_db(opts = None):
    """username/password and target can be stored in a database.
    If no username/password is known for a target, it is asked"""
    global _opts, target, email

    _opts = [] if opts is None else opts
    d = open_db()

    if not target and 'target' in d:
        target = d['target']

    for o,a in opts:
        if o == '-t':
            d['target'] = init_target(a)
        if o == '-e':
            errors(a)
            d['email'] = email
        if o == '-s':
            for k in d.keys():
                print(k + "=" + d[k])


    d.close()

def init_target(env = None):
    global target
    t = None
    if not env and 'ENV' in os.environ:
        t = os.environ['ENV']


    if t:
        target = environments[t]
    if not target:
        target = environments['test']

    return target

def init_logging():
    if 'DEBUG' in os.environ and os.environ['DEBUG']:
        logging.basicConfig(stream = sys.stderr, level=logging.DEBUG, format="%(asctime)-15s:%(levelname).3s:%(message)s")
    else:
        logging.basicConfig(stream = sys.stderr, level=logging.INFO, format="%(asctime)-15s:%(levelname).3s:%(message)s")


def opts(args = "t:e:srh", usage = None, minargs = 0, login = True, env = None, mail_errors = None, init_log = True):
    """Initialization with opts. Some argument handling"""
    if init_log:
        init_logging()
    try:
        opts, args = getopt.getopt(sys.argv[1:], args)
    except getopt.GetoptError as err:
        print(err)
        if usage is not None:
            usage()
        generic_usage()
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

    init_target(env)
    init_db(opts)


    if login:
        creds()
    return opts,args

lock = threading.Lock()

def creds(pref = ""):
    global authorizationHeader
    if authorizationHeader:
        #logging.debug("Already authorized")
        return

    with lock:
        d = open_db()
        if not target:
            raise Exception("No target defined")


        usernamekey = pref + target + ':username'
        passwordkey = pref + target + ':password'

        if not usernamekey in d  or ('-r','') in _opts :
            d[usernamekey] = input('Username for ' + target + ': ')
            d[passwordkey] = getpass.getpass()
            print("Username/password stored in file creds.db. Use -r to set it.")

        login(d[usernamekey], d[passwordkey])
        errors(d.get("email"))

        d.close()


def login(username, password):
    logging.debug("Logging in " + username)
    passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, target, username, password)
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(passman)))

    global authorizationHeader
    base64string = base64.encodebytes(('%s:%s' % (username, password)).encode()).decode()[:-1]
    authorizationHeader = "Basic %s" % base64string



def errors(mail=None):
    global email
    if email != mail:
        if mail:
            email = mail
            logging.debug("Emailing to " + email)
        else:
            email = None
            logging.debug("Not emailing")


def open_db():
    return shelve.open(os.path.join(get_poms_dir(), "creds"))

def generic_usage():
    print("-s       Show stored credentials (in creds.db). If none stored, username/password " +
        "will be asked interactively.")
    print("-t <url> Change target. 'test', 'dev' and 'prod' are " +
          "possible abbreviations for https://api[-test|-dev].poms.omroep.nl/media/. " +
          "Defaults to previously used version (stored in creds.db) or the environment variable 'ENV")
    print("-r       Reset and ask username/password again")
    print("-e <email> Set email address to mail errors to. " +
          "Defaults to previously used value (stored in creds.db).")

# private method to implement both members and episodes calls.
def _members_or_episodes(mid, what):
    creds()
    logging.info("loading members of " + mid)
    result = []
    offset = 0
    batch = 20
    while True:
        url = (target + 'media/group/' +  urllib.parse.quote(mid, '') + "/" + what + "?max=" + str(batch) +
               "&offset=" + str(offset))
        xml = _get_xml(url)
        items = xml.getElementsByTagName('item')
        result.extend(items)
        if len(items) == 0:
            break
        offset += batch
        #print xml.childNodes[0].toxml('utf-8')
        total = xml.childNodes[0].getAttribute("totalCount")
        logging.info(str(len(result)) + "/" + total)


    return result

def members(mid):
    """return a list of all members of a group. As XML objects, wrapped
    in 'items', so you can see the position"""
    return _members_or_episodes(mid, "members")

def episodes(mid):
    """return a list of all episodes of a group. As XML objects, wrapped
    in 'items', so you can see the position"""
    return _members_or_episodes(mid, "episodes")

def get_memberOf_xml(groupMid, position=0, highlighted="false"):
    """create an xml sniplet representing a memberOf"""
    return ('<memberOf position="' + str(position) + '" highlighted="' +
            highlighted + '">' + groupMid + '</memberOf>')

def add_member(groupMid, memberMid, position=0, highlighted="false"):
    """Adds a a member to a group"""
    url = target + "api/media/" + memberMid + "/memberOf"
    xml = get_memberOf_xml(groupMid, position, highlighted)
    response = urllib.request.urlopen(urllib.request.Post(url, data=xml))

def post_location(mid, programUrl, duration = None, bitrate = None, height=None, width=None, aspectRatio = None, format = None, publishStart = None, publishStop = None):
    if not format:
        format = guess_format(programUrl)

    xml = ("<location xmlns='urn:vpro:media:update:2009'" + date_attr("publishStart", publishStart) + date_attr("publishStop", publishStop) + ">" +
           "  <programUrl>" + programUrl + "</programUrl>" +
           "   <avAttributes>")
    if bitrate:
        xml += "<bitrate>" + str(bitrate) + "</bitrate>";
    if format:
        xml += "<avFileFormat>" + format + "</avFileFormat>";

    if height or width or aspectRatio:
        xml += "<videoAttributes "
        if height:
            xml += "height='" + height + "' "
        if width:
            xml += "width='" + width + "' "
        xml += ">"
        if aspectRatio:
            xml += "<aspectRatio>" + aspectRatio + "</aspectRatio>"
        xml += "</videoAttributes>"

    xml += "</avAttributes>"
    if duration:
        xml += "<duration>" + duration + "</duration>"

    xml += "</location >"
    logging.debug("posting " + xml)
    return post_to("media/media/" + mid + "/location", xml, accept = "text/plain")


def set_location(mid, location, publishStop = None, publishStart = None, programUrl = None):
    xml = get_locations(mid).toprettyxml()
    if location.isdigit():
        args = {"id": location}
        if programUrl:
            args["programUrl"] = programUrl
    else:
        args = {"programUrl": urllib.parse.unquote(location)}


    if publishStop:
        args['publishStop'] = date_attr_value(publishStop)
    if publishStart:
        args['publishStart'] = date_attr_value(publishStart)

    logging.debug("Found " + xml)
    location_xml = xslt(xml, get_xslt("location_set_publishStop.xslt"), args)
    if location_xml != "":
        logging.debug("posting " + location_xml)
        return post_to("media/media/" + mid + "/location", location_xml, accept = "text/plain")
    else:
        logging.debug("no location " + location)
        return "No location " + location


def get_xslt(name):
    return os.path.normpath(os.path.join(get_poms_dir(), "..", "xslt", name))

def get_poms_dir():
    return os.path.dirname(__file__)


def guess_format(url):
    if url.endswith(".mp4"):
        return "MP4"
    elif url.endswith(".mp3"):
        return "MP3"
    else:
        return "UNKNOWN"

def date_attr(name, datetime):
    if datetime:
        aware = datetime.replace(tzinfo=pytz.UTC)
        return " " + name + "='" + date_attr_value(datetime) + "'"
    else:
        return ""
def date_attr_value(datetime):
    if datetime:
        aware = datetime.replace(tzinfo=pytz.UTC)
        return aware.strftime("%Y-%m-%dT%H:%M:%SZ")
    return None


def post_str(xml):
    return post(minidom.parseString(xml).documentElement)

def parkpost_str(xml):
    return parkpost(minidom.parseString(xml).documentElement)


def get(mid, parser=minidom):
    """Returns XML-representation of a mediaobject"""
    creds()
    url = target + "media/media/" + urllib.parse.quote(mid)
    return _get_xml(url, parser=parser)


def get_locations(mid):
    creds()
    url = target + "media/media/" + urllib.parse.quote(mid) + "/locations"
    return _get_xml(url)

def xslt(xml, xslt_file, params= {}):
    args = ["xsltproc"]
    for key, value in params.items():
        args.extend(("--stringparam", key, value))
    args.extend((xslt_file, "-"))
    logging.debug(' '.join(args))
    p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stdin.write(xml.encode())
    output = p.communicate()
    return str(output[0].decode())


def _get_xml(url, parser=minidom):
    try:
        logging.info("getting " + url)
        req = urllib.request.Request(url)
        req.add_header("Accept", "application/xml")
        response = urllib.request.urlopen(req)
    except Exception as e:
        logging.error(url + " " + str(e))
        sys.exit(1)
    xmlBytes = response.read()
    xml = None
    try:
        if parser == ET:
            xml = ET.fromstring(xmlBytes)
        elif parser == minidom:
            xml = minidom.parseString(xmlBytes)
    except Exception:
        logging.error("Could not parse \n" + xmlBytes.decode(sys.stdout.encoding, "surrogateescape"))
    return xml



def add_genre(xml, genreId):
    """Adds a genre to the minidom object"""
    genreEl = xml.ownerDocument.createElement("genre")
    genreEl.appendChild(xml.ownerDocument.createTextNode(genreId))
    _append_element(xml, genreEl)


def add_image(mid, image, image_type="PICTURE", title=None):
    if os.path.isfile(image):
        with open(image, "rb") as image_file:
            if not title:
                title="Image for %s" % mid
            encoded_string = base64.b64encode(image_file.read()).decode("ascii")
            xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<image xmlns="urn:vpro:media:update:2009" type="%s">
  <title>%s</title>
  <imageData>
    <data>%s</data>
  </imageData>
</image>
""" % (image_type, title, encoded_string)
            logging.debug(xml)
            return post_to("media/media/" + mid + "/image", xml, accept="text/plain")



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


def post(xml, lookupcrid=False, followMerges=True):
    creds()
    # it seems minidom sucks a bit, since it should have added these attributes
    # automaticly of course. The xml is simply not valid otherwise
    xml.setAttribute("xmlns", "urn:vpro:media:update:2009")
    xml.setAttribute("xmlns:xsi",
                     "http://www.w3.org/2001/XMLSchema-instance")
    url = target + "media/media?lookupcrid=" + str(lookupcrid) + "&followMerges=" + str(followMerges)

    if email:
        url += "&errors=" + email


    #print xml.toxml()
    logging.debug("posting " + xml.getAttribute("mid") + " to " + url)
    req = urllib.request.Request(url, data=xml.toxml('utf-8'))
    return _post(req, accept = "text/plain")



def parkpost(xml):
    creds("parkpost:")
    url = target + "parkpost/promo"

    logging.info("posting to " + url)
    req = urllib.request.Request(url, data=xml.toxml('utf-8'))
    return _post(req)

def post_to(path, xml, accept="application/xml"):
    creds()
    url = target + path
    if type(xml) != str:
        xml = xml.toxml('utf-8')

    if email:
        url += "?errors=" + email
    req = urllib.request.Request(url, data = xml.encode())
    logging.debug("Posting to " + url)
    return _post(req, accept)


def _post(req, accept="application/xml"):
    req.add_header("Authorization", authorizationHeader);
    req.add_header("Content-Type", "application/xml")
    req.add_header("Accept", accept)
    #req.add_header("Accept", "application/json")
    #req.add_header("Accept", "text/plain")
    try:
        response = urllib.request.urlopen(req)
        return response.read().decode()
    except urllib.request.HTTPError as e:
        logging.error(e.read().decode())
        return None
