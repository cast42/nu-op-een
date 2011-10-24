# -*- coding: utf-8 -*-

import logging
import time
import datetime
import simplejson as json
import urllib2

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from google.appengine.api import memcache

#curl -H "accept-type: application/vnd.epg.vrt.be.schedule_2.4+json" http://services.vrt.be/epg/schedules/today?channel_code=O8

def rfc3339todate(timestamp):
    logging.debug("In rfc339todate");
    update = timestamp.rsplit('Z')[0]
    return datetime.datetime.strptime(update, '%Y-%m-%dT%H:%M:%S')

class MainPage(webapp.RequestHandler):
    def get(self,p):
        try:
            logging.debug('load feed')
            url = 'http://services.vrt.be/epg/schedules/today?channel_code=O8'
            result = ''
            txt = u''
            try:
                req = urllib2.Request(url)
                req.add_header('accept', 'application/vnd.epg.vrt.be.schedule_2.4+json')
                req.add_header('Content-Type', 'application/json')
                result = urllib2.urlopen(req)
                txt = result.read().decode("utf-8")
            except urllib2.HTTPError, e:
                self.response.out.write('The server couldn\'t fulfill the request.')
                self.response.out.write('Error code: ' + e.code)
            except urllib2.URLError, e:
                self.response.out.write('We failed to reach a server.')
                self.response.out.write('Reason: ' + e.reason)
                self.error(500)
                self.response.out.write('<h1>500 Server Error</h1><p>' + str(e.reason) + '</p>')
                logging.error(e.reason)
                return
            logging.debug('URL fetch done')
            obj = {}
            try:
                obj = json.loads(txt)
            except ValueError, e:
                logging.error('Error parsing json string %s\n%s', txt, e)
            events = obj['schedule']['events']
            #color gradient via http://www.colorzilla.com/gradient-editor/
            #from #58b9e4 to #F6FBF9
            prog = """<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    <style>
        img { max-width: 100%;}
        body {
            font-size: 24px;
            font-family: Arial,Helvetica,sans-serif;
            /* font-family: 'Lucida Grande', Verdana, sans-serif; */
            font-weight: bold;
            background: #58b9e4; /* Old browsers */
            background: -moz-linear-gradient(-45deg, #58b9e4 0%, #2989d8 0%, #58b9e4 0%, #f6fbf9 100%); /* FF3.6+ */
            background: -webkit-gradient(linear, left top, right bottom, color-stop(0%,#58b9e4), color-stop(0%,#2989d8), color-stop(0%,#58b9e4), color-stop(100%,#f6fbf9)); /* Chrome,Safari4+ */
            background: -webkit-linear-gradient(-45deg, #58b9e4 0%,#2989d8 0%,#58b9e4 0%,#f6fbf9 100%); /* Chrome10+,Safari5.1+ */
            background: -o-linear-gradient(-45deg, #58b9e4 0%,#2989d8 0%,#58b9e4 0%,#f6fbf9 100%); /* Opera 11.10+ */
            background: -ms-linear-gradient(-45deg, #58b9e4 0%,#2989d8 0%,#58b9e4 0%,#f6fbf9 100%); /* IE10+ */
            background: linear-gradient(-45deg, #58b9e4 0%,#2989d8 0%,#58b9e4 0%,#f6fbf9 100%); /* W3C */
            filter: progid:DXImageTransform.Microsoft.gradient( startColorstr='#58b9e4', endColorstr='#f6fbf9',GradientType=1 ); /* IE6-9 fallback on horizontal gradient */
        }
    </style>
</head>
<body>
    <center>
        <img alt="logo een" title="een" border="0" height="100" src="img/een.png" width="100">
    </center>
"""
            fmt = '%H:%M:%S'
            onAir = False
            for event in events:
                if event['onAir']:
                    prog += '<p>' + event['title'] + '</p>'
                    starttime = rfc3339todate(event['startTime'])
                    starttime = starttime + datetime.timedelta(hours=2)
                    prog += '<p>starts at ' + starttime.strftime(fmt) + '</p>'
                    endtime = rfc3339todate(event['endTime'])
                    endtime = endtime + datetime.timedelta(hours=2)
                    prog += '<p>ends at ' + endtime.strftime(fmt) + '</p><br>'
                    prog += '<img src="' + event['pictureUrl'] + '" />'
                    onAir = True
                    break
            if not onAir:
                prog = '<p>Geen uitzending momenteel</p>'
            prog += '</body></html>'
            self.response.headers['Content-Type'] = 'text/html'
            self.response.out.write(prog)
        except Exception, err:
            self.error(500)
            self.response.out.write('<h1>500 Server Error</h1><p>' + str(err) + '</p>\n')
            self.response.out.write('<p>prog=</p>')
            self.response.out.write('<p>' + prog + '</p>')
            self.response.out.write('<p>result from HTTP GET:</p>')
            self.response.out.write('<p>' + txt + '</p>')
            logging.error(err)

application = webapp.WSGIApplication([(r'/(.*)', MainPage)],debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
