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
from google.appengine.ext import ndb

# [END imports]

# [START Stream & Photo]
class Photo(ndb.Model):
    """Sub model for representing a photo."""
    title = ndb.StringProperty(indexed=True)
    comment = ndb.StringProperty(indexed=True)
    blob_key = ndb.BlobKeyProperty()
    url = ndb.StringProperty(indexed=True)
    date = ndb.DateTimeProperty(auto_now_add=True)
    loc = ndb.GeoPtProperty()
    parent_title = ndb.StringProperty()


class Stream(ndb.Model):
    """A main model for representing an individual stream entry."""
    owner = ndb.StringProperty()
    title = ndb.StringProperty()
    tags = ndb.StringProperty(repeated=True)
    cover_url = ndb.StringProperty()
    subscriber = ndb.StringProperty(repeated=True)
    #num_photos = ndb.IntegerProperty()
    num_views = ndb.IntegerProperty()
    last_modified_date = ndb.DateTimeProperty(auto_now=True)
    recent_access_freq = ndb.IntegerProperty()
    queue = ndb.DateTimeProperty(repeated=True)


# [END Stream & Photo]
