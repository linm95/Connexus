#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]

import json
import copy
import os
import urllib
import re
import datetime
import time
import jinja2
import webapp2
import global_vars as VAR
import sys
import random


from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.api import search
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import mail
from google.appengine.api import memcache

from database import *

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_STREAM_NAME = 'My Stream'

user_id = ""

# For image uploader
DEBUG = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
WEBSITE = 'https://blueimp.github.io/jQuery-File-Upload/'
MIN_FILE_SIZE = 1  # bytes
# Max file size is memcache limit (1MB) minus key size minus overhead:
MAX_FILE_SIZE = 999000  # bytes
IMAGE_TYPES = re.compile('image/(gif|p?jpeg|(x-)?png)')
ACCEPT_FILE_TYPES = IMAGE_TYPES
THUMB_MAX_WIDTH = 80
THUMB_MAX_HEIGHT = 80
THUMB_SUFFIX = '.' + str(THUMB_MAX_WIDTH) + 'x' + str(THUMB_MAX_HEIGHT) + '.png'
EXPIRATION_TIME = 300  # seconds
# If set to None, only allow redirects to the referer protocol+host.
# Set to a regexp for custom pattern matching against the redirect value:
REDIRECT_ALLOW_TARGET = None


class MailStat(ndb.Model):
    user_id = ndb.StringProperty()
    mailCnt = ndb.IntegerProperty()
    mailRate = ndb.StringProperty()


user_id = ""


class SuggestionCache(ndb.Model):
    term = ndb.StringProperty()
    suggestion = ndb.StringProperty(repeated=True, indexed=False)

# [START main_page]
class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            mailStat = MailStat.query(MailStat.user_id == user.user_id()).get()
            if mailStat:
                pass
            else:
                mailStat = MailStat()
                mailStat.user_id = user.user_id()
                mailStat.cnt = 0
                mailStat.mailRate = VAR.NO_REPORT
                mailStat.put()

            self.redirect(VAR.MANAGE_PAGE)
            return
        else:
            url = users.create_login_url(self.request.uri)

        template_values = {
            'url': url,
        }

        template = JINJA_ENVIRONMENT.get_template(VAR.LOGIN_HTML)
        self.response.write(template.render(template_values))


# [END main_page]


# [START ManageStream]
class ManageStream(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            own_streams_query = Stream.query(
                Stream.owner == user.user_id()).order(-Stream.last_modified_date)
            own_streams = own_streams_query.fetch(VAR.OWN_STREAMS_PER_PAGE)

            subscribed_streams_query = Stream.query(
                Stream.subscriber == user.email().lower()).order(-Stream.last_modified_date)
            subscribed_streams = subscribed_streams_query.fetch(
                VAR.SUB_STREAMS_PER_PAGE)

            for stream in own_streams:
                stream.num_photos = Photo.query(ancestor=stream.key).count()

            for stream in subscribed_streams:
                stream.num_photos = Photo.query(ancestor=stream.key).count()

            template_values = {
                'own_streams': own_streams,
                'subscribed_streams': subscribed_streams,
                'user': user.email()
            }
            template = JINJA_ENVIRONMENT.get_template(VAR.MANAGE_HTML)
            self.response.write(template.render(template_values))
        else:
            self.redirect(VAR.ROOT)


# [END ManageStream]

# [START DeleteStream]


class DeleteStream(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            # for all streams to be deleted
            streams_to_delete = self.request.get_all(VAR.DELETE_STREAMS)
            for stream_title in streams_to_delete:
                stream = Stream.query(Stream.title == stream_title).get()
                if stream:
                    # for all photos in a stream
                    photos = Photo.query(ancestor=stream.key).fetch()
                    index = search.Index(VAR.PHOTO_INDEX_NAME)
                    for photo in photos:
                        if hasattr(photo, 'stream_title'):
                            index.delete(document_ids = photo.stream_title)
                        photo.key.delete()

                    # Delete the document
                    index = search.Index(VAR.STREAM_INDEX_NAME)
                    doc_id = stream.title.replace(" ", "%")
                    index.delete(document_ids=doc_id)

                    # then delete stream itself
                    stream.key.delete()

                else:
                    self.redirect(VAR.ERROR_PAGE + '?' +
                                  VAR.ERROR_TYPE + '=no_stream')
                    return

            # redirect/refresh
            time.sleep(1)
            self.redirect(VAR.MANAGE_PAGE)
        else:
            self.redirect(VAR.ROOT)


# [END DeleteStream]

# [START UnsubscribeStream]


class UnsubscribeStream(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            # for all streams to be unsubscribed
            streams_to_unsubscribe = self.request.get(
                VAR.UNSUBSCRIBE_STREAMS, allow_multiple=True)
            for stream_title in streams_to_unsubscribe:
                stream = Stream.query(Stream.title == stream_title).get()
                if stream:
                    stream.subscriber.remove(user.email().lower())
                    stream.put()
                else:
                    self.redirect(VAR.ERROR_PAGE + '?' +
                                  VAR.ERROR_TYPE + '=no_stream')
                    return

            # redirect/refresh
            time.sleep(1)
            self.redirect(VAR.MANAGE_PAGE)
        else:
            self.redirect(VAR.ROOT)


# [END UnsubscribeStream]

# [START SubscribeStream]


class SubscribeStream(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            stream_title = self.request.get(VAR.STREAM_TITLE)
            stream = Stream.query(Stream.title == stream_title).get()

            if not (user.email().lower() in stream.subscriber):
                stream.subscriber.append(user.email().lower())
            stream.put()
            time.sleep(1)
            # print(stream.subscriber)
            self.redirect(VAR.VIEW_STREAM_PAGE + "?title=" +
                          stream_title + "&owner=" + stream.owner)


# [END SubscribeStream]


# [START ViewStream]
class ViewStream(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        stream_title = self.request.get(VAR.STREAM_TITLE)
        stream_owner = self.request.get(VAR.STREAM_OWNER)
        # get stream based on owner and title
        stream = Stream.query(Stream.title == stream_title).get()

        if stream:
            # increment view count
            stream.num_views += 1
            stream.put()

            # get all photos in stream
            photo_query = Photo.query(ancestor=stream.key).order(-Photo.date)

            # determine if we need a more_pics button
            show_more_pics_btn = (photo_query.count() > VAR.PHOTOS_PER_PAGE)

            # based on params in the request
            if (self.request.get(VAR.MORE_PICS)):
                photos = photo_query.fetch()
                show_more_pics_btn = False
            else:
                photos = photo_query.fetch(VAR.PHOTOS_PER_PAGE)
            # create upload url
            upload_url = blobstore.create_upload_url(VAR.UPLOAD_IMAGE_PAGE)

            template_values = {
                'photos': photos,
                'show_more_pics_btn': show_more_pics_btn,
                'stream': stream,
                'upload_url': upload_url,
                'user': user.email()
            }

            # Update the recent access frequency
            queue = stream.queue
            queue.append(datetime.datetime.now())
            stream.queue = queue
            stream.put()

            template = JINJA_ENVIRONMENT.get_template(VAR.VIEW_STREAM_HTML)
            self.response.write(template.render(template_values))

        else:
            self.redirect(VAR.ERROR_PAGE + '?' + VAR.ERROR_TYPE + '=no_stream')


# [END ViewStream]

class FixUpload(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user:
            stream_owner = self.request.get(VAR.STREAM_OWNER)
            if(stream_owner != user.user_id()):
                print("Unauthorize")
                self.redirect(VAR.ERROR_PAGE + '?' +
                              VAR.ERROR_TYPE + '=unauth_upload')
                return
        # create upload url
        upload_url = blobstore.create_upload_url(VAR.UPLOAD_IMAGE_PAGE)
        self.redirect(upload_url, code=307)


# [START UploadImage]


class UploadImage(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        user = users.get_current_user()
        if user:

            stream_owner = self.request.get(VAR.STREAM_OWNER)

            #print(self.request)
            if (stream_owner == user.user_id()):
                stream_title = self.request.get(VAR.STREAM_TITLE)

                # get stream based on owner and title
                stream = Stream.query(ndb.AND(Stream.owner == stream_owner,
                                              Stream.title == stream_title)).get()

                print blobstore.BlobInfoParseError
                try:

                    uploads = self.get_uploads(VAR.PHOTO)
                except blobstore.BlobInfoParseError:
                    self.redirect(VAR.ERROR_PAGE + '?' +
                                  VAR.ERROR_TYPE + '=md5')
                    return

                print len(uploads)
                if len(uploads) == 0:
                    self.redirect(VAR.ERROR_PAGE + '?' +
                                  VAR.ERROR_TYPE + '=no_photo')

                    return
                comments = ''
                for upload in uploads:
                    # add new photo
                    photo = Photo(parent=stream.key)
                    photo.title = upload.filename
                    photo.blob_key = upload.key()
                    photo.comment = self.request.get(VAR.PHOTO_COMMENTS)
                    photo.url = images.get_serving_url(upload.key())
                    photo.loc = ndb.GeoPt(random.uniform(-90, 90), random.uniform(-180, 180))
                    photo.parent_title = stream_title
                    photo.put()

                    comments += " " + photo.comment
                    #add new doc
                    fields = [
                        search.TextField(name = 'parent', value = photo.parent_title),
                        search.TextField(name = 'title', value = photo.title),
                        search.TextField(name = 'url', value = photo.url),
                        search.AtomField(name='all', value=VAR.MATCHCODE),
                        search.GeoField(name = 'location', value = search.GeoPoint(photo.loc.lat, photo.loc.lon))
                    ]
                    doc_id = photo.url
                    d = search.Document(doc_id = doc_id, fields = fields)
                    add_result = search.Index(name = VAR.PHOTO_INDEX_NAME).put(d)

                stream.put()

                #add photo comment to stream tag
                index = search.Index(name = VAR.STREAM_INDEX_NAME)
                doc_id = stream_title.replace(" ", "%")
                doc = index.get(doc_id)
                doc.fields[5] = search.TextField(name = 'tags', value = doc.fields[5].value + comments)
                index.put(doc)

                self.redirect(VAR.UPLOAD_IMAGES_PAGE, code=307)
                # self.redirect(VAR.VIEW_STREAM_PAGE + "?title=" +
                # stream_title + "&owner=" + stream.owner)

            else:
                self.error(403)
                self.redirect(VAR.ERROR_PAGE + '?' +
                              VAR.ERROR_TYPE + '=unauth_upload')
                # unauthorized request
        else:
            self.redirect(VAR.ROOT)


# [END UploadImage]

# [START CreateStream]


class CreateStream(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        template_values = {
            'user': user.email()
        }

        template = JINJA_ENVIRONMENT.get_template(VAR.CREATE_STREAM_HTML)
        self.response.write(template.render(template_values))

    def post(self):
        stream_title = self.request.get(VAR.STREAM_TITLE)
        if not stream_title:
            self.redirect(VAR.ERROR_PAGE + '?' +
                          VAR.ERROR_TYPE + '=empty_name')
            return
        dup_name = Stream.query(Stream.title == stream_title).count()
        if dup_name:
            self.redirect(VAR.ERROR_PAGE + '?' + VAR.ERROR_TYPE + '=dup_name')
            return

        stream = Stream()
        if users.get_current_user():
            stream.owner = users.get_current_user().user_id()
            stream.title = self.request.get(VAR.STREAM_TITLE)
            stream.tags = re.split(',\s*', self.request.get(VAR.STREAM_TAGS))
            cv_url = self.request.get(VAR.COVER_URL)
            if cv_url:
                stream.cover_url = self.request.get(VAR.COVER_URL)
            else:
                stream.cover_url = VAR.NO_IMAGE_URL
            stream.num_views = 0
            stream.subscriber = re.split(
                '\s*', self.request.get(VAR.STREAM_SUBSCRIBER).lower())
            stream.subscriber = list(set(stream.subscriber))
            stream.queue = list()
            stream.put()

            # add doc to index
            fields = [
                search.TextField(name='title', value=stream.title),
                search.TextField(name='url', value=stream.cover_url),
                search.NumberField(name='recentAccessFreq', value=0),
                search.DateField(name='creationTime',
                                 value=datetime.datetime.today()),
                search.AtomField(name='all', value=VAR.MATCHCODE),
                search.TextField(name='tags', value=self.request.get(VAR.STREAM_TAGS)),
                search.TextField(name='searchStr', value=getAllSubstrings(stream.title, False) + getAllSubstrings(
                    self.request.get(VAR.STREAM_TAGS), True))
            ]
            doc_id = stream.title.replace(" ", "%")
            d = search.Document(doc_id=doc_id, fields=fields)
            add_result = search.Index(name=VAR.STREAM_INDEX_NAME).put(d)

            time.sleep(1)
            self.redirect(VAR.MANAGE_PAGE)


# [END CreateStream]

# [START getSearchTags]
def getAllSubstrings(s, Tag):
    words = []
    if Tag:
        words = s.split(',')
    else:
        words = s.split(' ')
    toReturn = ''
    for word in words:
        substrs = getAllSubStringsAux(word)
        for substr in substrs:
            toReturn += substr + ' '
    return toReturn


def getAllSubStringsAux(s):
    length = len(s)
    return [s[i:j + 1] for i in xrange(length) for j in xrange(i, length)]


# [END getSearchTags]

# [START View]
class ViewPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        index = search.Index(VAR.STREAM_INDEX_NAME)
        sortops = search.SortOptions(expressions=[
            search.SortExpression(expression="creationTime",
                                  direction='ASCENDING', default_value=0)
        ])
        streams = []
        cursor = search.Cursor()
        query = "all= " + VAR.MATCHCODE
        while True:
            search_query = search.Query(
                query_string=query,
                options=search.QueryOptions(
                    limit=1000,
                    cursor=cursor,
                    sort_options=sortops
                )
            )
            results = index.search(search_query)
            cursor = results.cursor
            for doc in results:
                fields = doc.fields
                title = fields[0].value
                stream = Stream.query(Stream.title == title).get()
                streams.append(stream)

            if results.number_found <= 100:
                break

        template_values = {
            'streams': streams,
            'user': user.email()
        }
        template = JINJA_ENVIRONMENT.get_template(VAR.VIEW_HTML)
        self.response.write(template.render(template_values))


# [END View]

# [START Search]
class SearchPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        template_values = {
            'user': user.email()
        }
        template = JINJA_ENVIRONMENT.get_template(VAR.SEARCH_HTML)
        self.response.write(template.render(template_values))

    def post(self):
        user = users.get_current_user()
        queryTxt = self.request.get(VAR.SEARCH_QUERY)
        index = search.Index(VAR.STREAM_INDEX_NAME)
        queryOptions = search.QueryOptions(
            limit=5
        )
        query = search.Query(query_string=queryTxt, options=queryOptions)
        search_results = index.search(query)
        streams = []
        for doc in search_results:
            fields = doc.fields
            title = fields[0].value
            stream = Stream.query(Stream.title == title).get()
            streams.append(stream)

        template_values = {
            'streams': streams,
            'query': queryTxt,
            'user': user.email()
        }

        template = JINJA_ENVIRONMENT.get_template(VAR.SEARCH_HTML)
        self.response.write(template.render(template_values))


# [END Search]

# [START Trending]


class TrendingPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        global user_id
        user_id = user.user_id()
        streams = []
        topThree = getTopThree()
        for tp in topThree:
            stream = Stream.query(Stream.title == tp[0]).get()
            if stream:
                stream.recent_access_freq = tp[1]
                streams.append(stream)

        user = users.get_current_user()
        mailStat = MailStat.query(MailStat.user_id == user.user_id()).get()

        template_values = {
            'streams': streams,
            'reportRate': mailStat.mailRate,
            'user': user.email()
        }
        template = JINJA_ENVIRONMENT.get_template(VAR.TRENDING_HTML)
        self.response.write(template.render(template_values))


# [END Trending]


def getTopThree():
    index = search.Index(VAR.STREAM_INDEX_NAME)
    sortops = search.SortOptions(expressions=[
        search.SortExpression(expression="recentAccessFreq",
                              direction=search.SortExpression.DESCENDING, default_value=0)
    ])
    query = 'all= ' + VAR.MATCHCODE
    search_query = search.Query(
        query_string=query,
        options=search.QueryOptions(
            limit=3,
            sort_options=sortops
        )
    )
    results = index.search(search_query)
    topThree = []
    for doc in results:
        fields = doc.fields
        title = fields[0].value
        freq = fields[2].value
        topThree.append((title, int(freq)))

    return topThree


# [START updateAccessFreq]
def updateAccessFreq():
    streams = Stream.query().fetch()
    index = search.Index(VAR.STREAM_INDEX_NAME)
    for stream in streams:
        doc_id = stream.title.replace(" ", "%")
        doc = index.get(doc_id=doc_id)
        queue = stream.queue
        while len(queue) > 0:
            time = queue[0]
            dt = datetime.datetime.today() - time
            if (dt < datetime.timedelta(hours=1)):
                break
            queue.pop(0)
        stream.queue = queue
        stream.put()
        if (doc):
            fields = doc.fields
            fields[2] = search.NumberField(
                name='recentAccessFreq', value=len(stream.queue))
            doc_id = stream.title.replace(" ", "%")
            d = search.Document(doc_id=doc_id, fields=fields)
            add_result = index.put(d)


# [END updateAccessFreq]

# [START SendMail]


class SendMail(webapp2.RequestHandler):
    def get(self):
        global user_id
        mailStat = MailStat.query(MailStat.user_id == user_id).get()
        if mailStat:
            mailRate = mailStat.mailRate
            mailCnt = mailStat.mailCnt
            if mailRate == VAR.NO_REPORT:
                pass
            elif mailRate == VAR.REPORT_5MIN:
                sendMail()
                mailCnt = 0
            elif mailRate == VAR.REPORT_1HR:
                if mailCnt == 11:
                    sendMail()
                    mailCnt = 0
                else:
                    mailCnt += 1
            elif mailRate == VAR.REPORT_1DAY:
                if mailCnt == 287:
                    sendMail()
                    mailCnt = 0
                else:
                    mailCnt += 1
            else:
                print "mailRate error"
            mailStat.mailCnt = mailCnt
            mailStat.put()


# [END SendMail]

# [START sendMail]


def sendMail():
    message = mail.EmailMessage(
        sender='linm9518@gmail.com',
        subject="Top 3 Trending Streams Update")
    message.to = "TA <ee382vta@gmail.com>"
    body = ""
    topThree = getTopThree()
    for tp in topThree:
        body += "  " + tp[0] + ": " + str(tp[1]) + " views" "\n"
    message.body = """Hello:

    This is a reminder mail from Wabler team.

    The Top 3 Trending Streams in past one hour are:
""" + body + """
The Wabler team
""" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message.send()


# [END sendMail]

# [START Report]
class Report(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        mailStat = MailStat.query(MailStat.user_id == user.user_id()).get()
        mailRate = self.request.get(VAR.REPORT_RATE)
        mailStat.mailRate = mailRate
        mailStat.put()
        self.redirect(VAR.TRENDING_PAGE)


# [START TrendingUpdate]


class TrendingUpdate(webapp2.RequestHandler):
    def get(self):
        updateAccessFreq()


# [END TrendingUpdate]

# [START LogOff]


class LogOff(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect(users.create_logout_url('/'))


# [END LogOff]

# [START ErrorPage]


class ErrorPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        error_type = self.request.get(VAR.ERROR_TYPE)
        if error_type == 'dup_name':
            error_message = """Error: you tried to create a new stream
                whose name is the same as an existing stream;
                operation did not complete"""
        elif error_type == 'empty_name':
            error_message = """Error: you tried to create a new stream
                whose name is an empty string; operation did not complete"""
        elif error_type == 'unauth_upload':
            error_message = """Error: you tried to upload a photo
                to a stream owned by others; operation did not complete"""
        elif error_type == 'no_photo':
            error_message = """Error: you did not select photo when uploading;
                operation did not complete"""
        elif error_type == 'no_stream':
            error_message = """Error: you tried to access a stream
                that does not exist; operation did not complete"""
        elif error_type == 'md5':
            error_message = """It seems your photo does not have md5 information,
                maybe try another photo; operation did not complete"""

        template_values = {'message': error_message,
                           'user': user.email()
                           }

        template = JINJA_ENVIRONMENT.get_template(VAR.ERROR_HTML)
        self.response.write(template.render(template_values))


# [END ErrorPage]

# [START SocialPage]


class SocialPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        template_values = {'user': user.email()
                           }
        template = JINJA_ENVIRONMENT.get_template(VAR.SOCIAL_HTML)
        self.response.write(template.render(template_values))


# [END SocialPage]

# [START GeoView]
class GeoView(webapp2.RequestHandler):
    def get(self):
        title = self.request.get(VAR.STREAM_TITLE)
        stream = Stream.query(Stream.title == title).get()
        if stream:
            photo_range = datetime.timedelta(365)
            utcNow = datetime.datetime.utcnow()
            now = datetime.datetime.now() - datetime.timedelta(hours=6)
            photos = Photo.query(ancestor=stream.key).fetch()
            days = []
            for photo in photos :
                td = utcNow - photo.date
                t0 = now - td
                if t0.year == now.year and t0.month == now.month and t0.day == now.day:
                    days.append(td.days)
                else:
                    days.append(td.days + 1)
            template_values = {
                'days': days,
                'photos': photos,
                'num_photos': len(photos),
            }
            template = JINJA_ENVIRONMENT.get_template(VAR.GEOVIEW_HTML)
            self.response.write(template.render(template_values))

# [END GeoView]


# [START AutoComplete]
class AutoComplete(webapp2.RequestHandler):
    def get(self):
        from webapp2_extras import json
        term = self.request.get("term").lower()
        cache = SuggestionCache.query(SuggestionCache.term == term).get()
        obj = []
        if cache:
            obj = cache.suggestion
        else:
            cache = SuggestionCache()
            cache.term = term
            results = Stream.query().fetch()
            for result in results:
                if term in result.title.lower():
                    obj.append(result.title)

                for tag in result.tags:
                    if term in tag.lower():
                        obj.append(tag)
            obj.sort()
            obj = obj[:20]
            cache.suggestion = obj
            cache.put()
        self.response.content_type = 'application/json'
        self.response.write(json.encode(obj))


# [END AutoComplete]

# [START UpdateCache]
class UpdateCache(webapp2.RedirectHandler):
    def get(self):
        caches = SuggestionCache.query().fetch()
        for cache in caches:
            cache.key.delete()


# [END UpdateCache]


class CORSHandler(blobstore_handlers.BlobstoreUploadHandler):
    def cors(self):
        headers = self.response.headers
        headers['Access-Control-Allow-Origin'] = '*'
        headers['Access-Control-Allow-Methods'] = \
            'OPTIONS, HEAD, GET, POST, DELETE'
        headers['Access-Control-Allow-Headers'] = \
            'Content-Type, Content-Range, Content-Disposition'

    def initialize(self, request, response):
        super(CORSHandler, self).initialize(request, response)
        self.cors()

    def json_stringify(self, obj):
        return json.dumps(obj, separators=(',', ':'))

    def options(self, *args, **kwargs):
        pass


class UploadHandler(CORSHandler):
    def validate(self, file):
        if file['size'] < MIN_FILE_SIZE:
            file['error'] = 'File is too small'
        elif file['size'] > MAX_FILE_SIZE:
            file['error'] = 'File is too big'
        elif not ACCEPT_FILE_TYPES.match(file['type']):
            file['error'] = 'Filetype not allowed'
        else:
            return True
        return False

    def validate_redirect(self, redirect):
        if redirect:
            if REDIRECT_ALLOW_TARGET:
                return REDIRECT_ALLOW_TARGET.match(redirect)
            referer = self.request.headers['referer']
            if referer:
                from urlparse import urlparse
                parts = urlparse(referer)
                redirect_allow_target = '^' + re.escape(
                    parts.scheme + '://' + parts.netloc + '/'
                )
            return re.match(redirect_allow_target, redirect)
        return False

    def get_file_size(self, file):
        file.seek(0, 2)  # Seek to the end of the file
        size = file.tell()  # Get the position of EOF
        file.seek(0)  # Reset the file position to the beginning
        return size

    def write_blob(self, data, info):
        key = urllib.quote(info['type'].encode('utf-8'), '') + \
              '/' + str(hash(data)) + \
              '/' + urllib.quote(info['name'].encode('utf-8'), '')
        try:
            memcache.set(key, data, time=EXPIRATION_TIME)
        except:  # Failed to add to memcache
            return (None, None)
        thumbnail_key = None
        if IMAGE_TYPES.match(info['type']):
            try:
                img = images.Image(image_data=data)
                img.resize(
                    width=THUMB_MAX_WIDTH,
                    height=THUMB_MAX_HEIGHT
                )
                thumbnail_data = img.execute_transforms()
                thumbnail_key = key + THUMB_SUFFIX
                memcache.set(
                    thumbnail_key,
                    thumbnail_data,
                    time=EXPIRATION_TIME
                )
            except:  # Failed to resize Image or add to memcache
                thumbnail_key = None
        return (key, thumbnail_key)

    def handle_upload(self):

        results = []
        i = 0
        for name, fieldStorage in self.request.POST.items():
            # for fieldStorage in tmpRequest:
            if type(fieldStorage) is unicode:
                continue
            result = {}
            result['name'] = urllib.unquote(fieldStorage.filename)
            result['type'] = fieldStorage.type
            result['size'] = self.get_file_size(fieldStorage.file)
            if self.validate(result):
                key, thumbnail_key = self.write_blob(
                    fieldStorage.value,
                    result
                )

                if key is not None:

                    result['url'] = self.request.host_url + VAR.UPLOAD_IMAGES_PAGE + '/' + key
                    result['deleteUrl'] = result['url']
                    result['deleteType'] = 'DELETE'
                    result['thumbnailUrl'] = result['url']

                    if thumbnail_key is not None:
                        result['thumbnailUrl'] = self.request.host_url + VAR.UPLOAD_IMAGES_PAGE + \
                                                 '/' + thumbnail_key

            else:
                result['error'] = 'Failed to store uploaded file.'
            results.append(result)

        return results

    def head(self):
        pass

    def get(self):
        self.redirect(WEBSITE)

    def post(self):

        if (self.request.get('_method') == 'DELETE'):
            return self.delete()
        result = {'files': self.handle_upload()}
        s = self.json_stringify(result)
        redirect = self.request.get('redirect')
        if self.validate_redirect(redirect):
            return self.redirect(str(
                redirect.replace('%s', urllib.quote(s, ''), 1)
            ))
        if 'application/json' in self.request.headers.get('Accept'):
            self.response.headers['Content-Type'] = 'application/json'
        self.response.write(s)


class FileHandler(CORSHandler):
    def normalize(self, str):
        return urllib.quote(urllib.unquote(str), '')

    def get(self, content_type, data_hash, file_name):
        content_type = self.normalize(content_type)
        file_name = self.normalize(file_name)
        key = content_type + '/' + data_hash + '/' + file_name
        data = memcache.get(key)
        if data is None:
            return self.error(404)
        # Prevent browsers from MIME-sniffing the content-type:
        self.response.headers['X-Content-Type-Options'] = 'nosniff'
        content_type = urllib.unquote(content_type)
        if not IMAGE_TYPES.match(content_type):
            # Force a download dialog for non-image types:
            content_type = 'application/octet-stream'
        elif file_name.endswith(THUMB_SUFFIX):
            content_type = 'image/png'
        self.response.headers['Content-Type'] = content_type
        # Cache for the expiration time:
        self.response.headers['Cache-Control'] = 'public,max-age=%d' \
                                                 % EXPIRATION_TIME
        self.response.write(data)

    def delete(self, content_type, data_hash, file_name):

        content_type = self.normalize(content_type)
        file_name = self.normalize(file_name)
        key = content_type + '/' + data_hash + '/' + file_name
        result = {key: memcache.delete(key)}
        content_type = urllib.unquote(content_type)
        if IMAGE_TYPES.match(content_type):
            thumbnail_key = key + THUMB_SUFFIX
            result[thumbnail_key] = memcache.delete(thumbnail_key)
        if 'application/json' in self.request.headers.get('Accept'):
            self.response.headers['Content-Type'] = 'application/json'
        s = self.json_stringify(result)
        self.response.write(s)
