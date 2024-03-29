from resources.lib.handler.hosterHandler import cHosterHandler
from resources.lib.handler.requestHandler import cRequestHandler
from resources.lib.parser import cParser
from resources.lib.gui.gui import cGui
from hosters.hoster import iHoster
from base64 import b64decode
from time import time
from time import sleep
from random import randint
from xbmc import log
from xbmc import LOGERROR
from xbmc import LOGDEBUG

try:
  from json import loads
except ImportError:
  from simplejson import loads

class cHoster(iHoster):

  FILE_INFO_URL = "http://www.putlocker.com/get_file.php?embed_stream="

  def __init__(self):
    self.__sDisplayName = 'Putlocker.com'
    self.__sFileName = self.__sDisplayName

  def getDisplayName(self):
    return  self.__sDisplayName

  def setDisplayName(self, sDisplayName):
    self.__sDisplayName = sDisplayName

  def setFileName(self, sFileName):
    self.__sFileName = sFileName

  def getFileName(self):
    return self.__sFileName

  def getPluginIdentifier(self):
    return 'putlocker'

  def isDownloadable(self):
    return True

  def isJDownloaderable(self):
    return True

  def getPattern(self):
    return 'flashvars.file=\"([^\"]+)\"';

  def getHosterLinkPattern(self):
    return '<a href="(http://www.putlocker.com/[^"]+)"'

  def setUrl(self, sUrl):
    self.__sUrl = sUrl

  def checkUrl(self, sUrl):
    return True

  def getUrl(self):
    return self.__sUrl

  def getMediaLink(self):
    return self.__getMediaLinkForGuest()



  def __getMediaLinkForGuest(self):
    log("Generate direct media link from %s" % self.__sUrl)

    # Get the video id from the link
    sPattern = '(?:http://www.putlocker.com)?/(?:file|embed)?/(.*?)$'
    oParser = cParser()
    aResult = oParser.parse(self.__sUrl, sPattern)

    if not aResult[0]:
      log("The link does not contain a media id.", LOGERROR)
      return [False, ""]

    log("Media ID: %s" % aResult[1][0])

    sMediaID = aResult[1][0]

    # First call the main page for the media.
    oRequest = cRequestHandler(self.__sUrl)
    sHtmlContent = oRequest.request()

    # We have to click on a button and create a valid cookie before we can call the settings with
    # the video link.

    # First call the main page for the media.
    oRequest = cRequestHandler(self.__sUrl)
    sHtmlContent = oRequest.request()


    #get session_hash
    hashPattern = 'value="([0-9a-f]+?)" name="hash"'
    aResult = oParser.parse(sHtmlContent, hashPattern)

    if aResult[0]:
        sPhpSessionId = aResult[1][0]
    else:
        log('putlocker: session hash not found')
        return False

    #post session_hash
    try:
        oRequest = cRequestHandler(self.__sUrl)
        oRequest.setRequestType(cRequestHandler.REQUEST_TYPE_POST)
        oRequest.addParameters('hash', sPhpSessionId)
        oRequest.addParameters('confirm', 'Continue as Free User')
        sHtmlContent = oRequest.request()
        log(sHtmlContent)
    except Exception, e:
        log('putlocker: got http error %d posting %s' % (e, self.__sUrl))
        return False

    # Get the session id of the last request.
    #aHeader = oRequest.getResponseHeader()
    #sPhpSessionId = self.__getPhpSessionId(aHeader)
    #if sPhpSessionId == False:
    #    log('BU')
    #    return [False,""]

    # Parse all needed data from the submit form. (Cause of the damn waiting button.)
    sPostName = ""
    sPostValue = ""
    sPostButtonName = ""
    sPattern = '<form.*?<input type="hidden" value="([^"]+)" name="([^"]+)".*?<input name="([^"]+)"'
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sPattern)
    if (aResult[0] == True):
        for aEntry in aResult[1]:
            sPostValue = aEntry[0]
            sPostName = aEntry[1]
            sPostButtonName = aEntry[2]

    log("Form data: %s %s %s" % (sPostName, sPostValue, sPostButtonName), LOGDEBUG)

    sPattern = 'var countdownNum.*?=(.*?);'
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sPattern)

    if not aResult[0]:
        log("No Time value found.", LOGERROR)
        sSecondsForWait = 5
    else:
        log("Seconds to wait: %s" % str(aResult[1][0]).replace(' ', ''), LOGDEBUG)
        sTicketValue = str(aResult[1][0]).replace(' ', '');
        sSecondsForWait = int(sTicketValue)

    # Waiting until we are allowed to go on.
    oGui = cGui()
    for i in range(sSecondsForWait,1,-1):
        oGui.showNofication(i, 1)
        sleep(1)
    oGui.showNofication(1, 1)

    # Calculate the cookie values.
    rndX = randint(1, 99999999 - 10000000) + 10000000
    rndY = randint(1, 999999999 - 100001000) + 100000000
    ts1 = float(time())
    ts2 = float(time())
    ts3 = float(time())
    ts4 = float(time())
    ts5 = float(time())

    sCookieValue = sPhpSessionId +'; '

    sCookieValue += '__utma=163708862.877577721.1313656417.1315132063.1318190394.10; __utmz=163708862.1318190394.10.10.utmcsr=iload.to|utmccn=(referral)|utmcmd=referral|utmcct=/de/title/388823-Alles-koscher-/; __utmb=163708862.2.10.1318190394; __utmc=163708862'

    #sCookieValue = sCookieValue + '__utma=' + str(rndY) + '.' + str(rndX) + '.' + str(ts1) + '.' + str(ts2) + '.' + str(ts3) + '.1; '
    #sCookieValue = sCookieValue + '__utmz=' + str(rndY) + '.' + str(ts4) + '.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); '
    #sCookieValue = sCookieValue + '__utmb=' + str(rndY) + '.1.10.' + str(ts3) + '; '
    #sCookieValue = sCookieValue + '__utmc=' + str(rndY) + "; "

    log("Prepared Cookie: %s" % sCookieValue, LOGDEBUG)

    # Construct the request.
    oRequest = cRequestHandler(self.__sUrl)
    oRequest.setRequestType(cRequestHandler.REQUEST_TYPE_POST)
    oRequest.addHeaderEntry('Cookie', sCookieValue)
    oRequest.addParameters(sPostName, sPostValue)
    oRequest.addParameters(sPostButtonName, '')
    sHtmlContent = oRequest.request()

    # Now we can try to get the id.
    log("Prepared config URL: %s" % cHoster.FILE_INFO_URL + sMediaID)

    oRequest = cRequestHandler(cHoster.FILE_INFO_URL + sMediaID)
    oRequest.addHeaderEntry('Referer', 'http://www.putlocker.com/')
    oRequest.addHeaderEntry('Cookie', sCookieValue)
    sHtmlContent = oRequest.request()
    print(sHtmlContent)
    sPattern = '<media:content.*?url="(.*?)"'
    oParser = cParser()
    aResult = oParser.parse(sHtmlContent, sPattern)

    # Try to load the datas from the sHtmlContent. This data should be json styled.
    if not aResult[0]:
      log("No config for this media id.", LOGERROR)
      return [False, ""]

    log("Generated direct media link %s" % aResult[1][0])

    return [True, aResult[1][0]]

  def __getPhpSessionId(self, aHeader):
    sReponseCookie = aHeader.getheader("Set-Cookie")
    try:
        aResponseCookies = sReponseCookie.split(";")
        return aResponseCookies[0]
    except:
        return False
