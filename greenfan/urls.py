#
#   Copyright 2012 Cisco Systems, Inc.
#
#   Author: Soren Hansen <sorhanse@cisco.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^logs/(?P<job_id>\d+)/(?P<log_name>\w+)/$', 'greenfan.views.job_log', name='job_log'),
    url(r'^logs/(?P<job_id>\d+)/$', 'greenfan.views.job_logs', name='job_logs'),
    url(r'^jobs/(?P<job_id>\d+)/$', 'greenfan.views.job_detail', name='job_detail'),
    url(r'^jobs/$', 'greenfan.views.jobs_list', name='jobs_list'),
    url(r'^hardware/$', 'greenfan.views.hardware_list', name='hardware_list'),
    url(r'^hardware_profiles/$', 'greenfan.views.hardware_profile_list', name='hardware_profile_list'),
    url(r'^hardware_profiles/(?P<name>.+)/$', 'greenfan.views.hardware_profile_detail', name='hardware_profile_detail'),
    url(r'^tests/$', 'greenfan.views.test_specification_list', name='test_specification_list'),
    url(r'', 'greenfan.views.front_page'),
)
