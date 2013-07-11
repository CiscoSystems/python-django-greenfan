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
import json
from itertools import islice
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404

from greenfan.models import Server, HardwareProfile, HardwareProfileTag, TestSpecification, Job

def job_log(request, job_id, log_name):
    job = get_object_or_404(Job, pk=job_id)
    return HttpResponse(job.get_log(log_name).read(), 'text/plain')

def job_logs(request, job_id):
    job = get_object_or_404(Job, pk=job_id)
    log_fps = job.get_all_logs()
    logs = {}
    for log in log_fps:
        fp = log_fps[log]
        if log in request.GET:
            offset, whence = int(request.GET.get(log)), 0
            fp.seek(offset, whence)
        elif 'tail' in request.GET:
            fp.seek(0, 2)
            size = fp.tell()
            offset, whence = -min(int(request.GET['tail']), size), 2
            fp.seek(offset, whence)
        logs[log] = fp.read()
    return HttpResponse(json.dumps(logs), 'text/json')

def job_detail(request, job_id):
    job = Job.objects.get(pk=job_id)
    if ((request.META.get('HTTP_X_REQUESTED_WITH', '') == 'XMLHttpRequest') or
        (request.GET.get('format', '') == 'json')):
        return HttpResponse(json.dumps({'id': job.id,
                                        'step': job.get_step_display(),
                                        'state': job.get_state_display()}), 'text/json')
    return render(request, 'job_detail.html',
                  {'job': job})

def jobs_list(request):
    if request.method == "POST":
        if request.POST.get('action', '') == 'create_job_from_testspec':
            ts = TestSpecification.objects.get(pk=request.POST['testspec_id'])
            job = ts.create_job()
            return HttpResponseRedirect(reverse('job_detail', kwargs={'job_id': job.id}))
    jobs = Job.objects.all()
    return render(request, 'jobs_list.html',
                  {'jobs': jobs})

def test_specification_list(request):
    specs = TestSpecification.objects.all()
    return render(request, 'test_specification_list.html',
                  {'specs': specs})

def hardware_profile_detail(request, name):
    profile = get_object_or_404(HardwareProfile, name=name)
    return render(request, 'hardware_profile_detail.html',
                  {'profile': profile})

def hardware_profile_list(request):
    profiles = HardwareProfile.objects.order_by('name')
    tags = HardwareProfileTag.objects.order_by('name')
    return render(request, 'hardware_profile_list.html',
                  {'profiles': profiles,
                   'tags': tags})

def hardware_list(request):
    servers = Server.objects.order_by('name')
    return render(request, 'hardware_list.html',
                  {'servers': servers})

def front_page(request):
    return render(request, 'front.html')
