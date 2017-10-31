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
import webapp2
import global_vars as VAR
import web_service
import android_service
# [END imports]

# [START app]
app = webapp2.WSGIApplication([
    (VAR.ROOT, web_service.MainPage),
    (VAR.MANAGE_PAGE, web_service.ManageStream),
    (VAR.DELETE_STREAM_PAGE, web_service.DeleteStream),
    (VAR.UNSUBSCRIBE_STREAM_PAGE, web_service.UnsubscribeStream),
    (VAR.CREATE_STREAM_PAGE, web_service.CreateStream),
    (VAR.VIEW_STREAM_PAGE, web_service.ViewStream),
    (VAR.VIEW_PAGE, web_service.ViewPage),
    (VAR.SEARCH_PAGE, web_service.SearchPage),
    (VAR.TRENDING_PAGE, web_service.TrendingPage),
    (VAR.ERROR_PAGE, web_service.ErrorPage),
    (VAR.SUBSCRIBE_PAGE, web_service.SubscribeStream),
    (VAR.LOGOFF, web_service.LogOff),
    (VAR.TRENDING_UPDATE_PAGE, web_service.TrendingUpdate),
    (VAR.SENDING_MAIL_PAGE, web_service.SendMail),
    (VAR.REPORT_PAGE, web_service.Report),
    (VAR.SOCIAL_PAGE, web_service.SocialPage),
    (VAR.AUTOCOMPLETE_PAGE, web_service.AutoComplete),
    (VAR.UPDATE_CACHE_PAGE, web_service.UpdateCache),
    (VAR.UPLOAD_IMAGES_PAGE, web_service.UploadHandler),
    (VAR.UPLOAD_IMAGE_PAGE, web_service.UploadImage),
    (VAR.UPLOAD_IMAGES_PAGE + '/(.+)/([^/]+)/([^/]+)', web_service.FileHandler),
    (VAR.FIX_UPLOAD_PAGE, web_service.FixUpload),
    (VAR.GEOVIEW_PAGE, web_service.GeoView),
    (VAR.ALL_STREAM_ANDROID, android_service.AllStreamView),
    (VAR.APP_UPLOAD_PAGE, android_service.AppUploadImage),
    (VAR.SINGLE_STREAM_ANDROID, android_service.SingleStreamView),
    (VAR.APP_SEARCH_PAGE, android_service.AppSearchPage),
    (VAR.APP_SEARCH_NEARBY, android_service.AppSearchNearby),
    (VAR.SUBSCRIBE_ANDROID, android_service.SubscribedStreamView),
    (VAR.APP_FIX_PAGE, android_service.FixAppUpload)
], debug=True)
# [END app]
