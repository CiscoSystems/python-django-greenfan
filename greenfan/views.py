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
from django.shortcuts import render, get_object_or_404

from greenfan.models import Server, HardwareProfile, HardwareProfileTag, TestSpecification

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
