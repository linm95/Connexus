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
import logging
import webapp2
import json
import global_vars as VAR
from google.appengine.ext import blobstore
from google.appengine.api import users
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.api import search
import random
import math

from database import *


# [END imports]

# [START AllStreamView]
class AllStreamView(webapp2.RequestHandler):
    def get(self):
        query = Stream.query().order(-Stream.last_modified_date)
        streams = query.fetch(16, projection=[Stream.cover_url, Stream.title])
        streams_dict = map(lambda x: x.to_dict(), streams)
        self.response.write(json.dumps(streams_dict))

# [END AllStreamView]


# [START SubscribedStreamView]
class SubscribedStreamView(webapp2.RequestHandler):
    def get(self):
        user_email = self.request.get(VAR.STREAM_OWNER)
        query = Stream.query(Stream.subscriber == user_email.lower()).order(-Stream.last_modified_date)
        streams = query.fetch(16, projection=[Stream.cover_url, Stream.title])
        streams_dict = map(lambda x: x.to_dict(), streams)
        self.response.write(json.dumps(streams_dict))

# [END SubscribedStreamView]

class FixAppUpload(webapp2.RequestHandler):
    def get(self):
        # create upload url
        upload_url = blobstore.create_upload_url(VAR.APP_UPLOAD_PAGE)
        self.response.write(upload_url)



class AppUploadImage(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        user = self.request.get(VAR.USER_ID)
        if user:
            stream_title = self.request.get(VAR.STREAM_TITLE)
            stream = Stream.query(Stream.title == stream_title).get()


            print(self.request)
            ## REMEMBER TO FIX HERE
            if (stream.owner == user):
            #if True:
                stream_title = self.request.get(VAR.STREAM_TITLE)
                # get stream based on owner and title
                stream = Stream.query(ndb.AND(Stream.owner == stream.owner,
                Stream.title == stream_title)).get()

                try:

                    uploads = self.get_uploads(VAR.UPLOAD_PHOTO)
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
                    photo.loc = ndb.GeoPt(self.request.get(VAR.LATITUDE), self.request.get(VAR.LONGITUDE))
                    photo.parent_title = stream_title
                    photo.put()

                    comments += " " + photo.comment
                    #add new doc
                    fields = [
                        search.TextField(name = 'parent', value = photo.parent_title),
                        search.TextField(name = 'title', value = photo.title),
                        search.TextField(name = 'url', value = photo.url),
                        search.AtomField(name = 'all', value = VAR.MATCHCODE),
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

                #self.redirect(VAR.UPLOAD_IMAGES_PAGE, code=307)
                # self.redirect(VAR.VIEW_STREAM_PAGE + "?title=" +
                # stream_title + "&owner=" + stream.owner)
            else:
                # unauthorized request
                self.error(403)


        else:
            print "No user found!!!"
            self.redirect(VAR.ROOT)


# [START AppSearchPage]
class AppSearchPage(webapp2.RequestHandler):
    def get(self):
        pass

    def post(self):
        queryTxt = self.request.get("query")
        # logging.info("queryTxt:" + queryTxt)
        index = search.Index(VAR.STREAM_INDEX_NAME)
        query = search.Query(query_string=queryTxt)
        search_results = index.search(query)
        streams = []
        for doc in search_results:
            fields = doc.fields
            title = fields[0].value
            url = fields[1].value
            streams.append({"title": title, "url": url})

        obj = {
            'streamList': streams
        }
        self.response.write(json.dumps(obj))


# [END AppSearchPage]

# [START SingleStreamView]
class SingleStreamView(webapp2.RequestHandler):
    def get(self):
        stream_title = self.request.get(VAR.STREAM_TITLE)
        page_number = self.request.get(VAR.SINGLE_STREAM_PAGE_NO)

        stream = Stream.query(Stream.title == stream_title).get()
        query = Photo.query(ancestor=stream.key).order(-Photo.date)
        photos = query.fetch(16, offset=16*int(page_number), projection=[Photo.url, Photo.title])
        photos_dict = map(lambda x: x.to_dict(), photos)
        self.response.write(json.dumps(photos_dict))

# [END SingleStreamView]

# [START SearchNeatby]
class AppSearchNearby(webapp2.RequestHandler):
    def get(self):

        '''
        user_location = {'lat': 30.000, 'lon': 32.000}
        '''

        lat = float(self.request.get('lat'))
        lng = float(self.request.get('lng'))
        page_number = int(self.request.get(VAR.SINGLE_STREAM_PAGE_NO))
        index = search.Index(name = VAR.PHOTO_INDEX_NAME)
        loc_expr = "distance(location, geopoint(%f, %f))" % (
            lat, lng)
        sortexpr = search.SortExpression(
            expression=loc_expr,
            direction=search.SortExpression.ASCENDING, default_value=45001)
        search_query = search.Query(
            query_string='all= ' + VAR.MATCHCODE,
            options=search.QueryOptions(
                limit = 16,
                offset=16*page_number,
                sort_options=search.SortOptions(expressions=[sortexpr])))
        docs = index.search(search_query)

        results = []

        for doc in docs:
            fields = doc.fields
            result = {}
            logging.info(fields)
            result['url'] = fields[2].value
            photoPoint = (fields[4].value.latitude, fields[4].value.longitude)
            result['distance'] = distance((lat,lng), photoPoint)
            result['parent'] = fields[0].value
            results.append(result)

        '''
        results = [
            {
                'url' : 'www.xxxxx.com'
                'distance' : 100.00
            },
            {
                'url' : 'www.xxxxx.com'
                'distance' : 100.00
            },
            .
            .
            .
        ]
        unit of distance: meter
        '''

        self.response.write(json.dumps(results))

# [END SearchNearby]

# [START distance]
def distance(loc1, loc2):
    lat1, lon1 = loc1
    lat2, lon2 = loc2
    earthRadius = 6371000.0 #m

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = earthRadius * c
    return d
# [END distance]
