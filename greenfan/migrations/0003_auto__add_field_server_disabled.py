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
# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Server.disabled'
        db.add_column('greenfan_server', 'disabled',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Server.disabled'
        db.delete_column('greenfan_server', 'disabled')


    models = {
        'greenfan.configuration': {
            'Meta': {'object_name': 'Configuration'},
            'admin_password': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'admin_user': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'gateway': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nameservers': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'netmask': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'ntp_servers': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'proxy': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'subnet': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'})
        },
        'greenfan.hardwareprofile': {
            'Meta': {'object_name': 'HardwareProfile'},
            'description': ('jsonfield.fields.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['greenfan.HardwareProfileTag']", 'symmetrical': 'False'})
        },
        'greenfan.hardwareprofiletag': {
            'Meta': {'object_name': 'HardwareProfileTag'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'})
        },
        'greenfan.server': {
            'Meta': {'object_name': 'Server'},
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hardware_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['greenfan.HardwareProfile']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'mac': ('django.db.models.fields.CharField', [], {'max_length': '17'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'power_address': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'power_id': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'power_password': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'power_type': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'power_user': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'greenfan.testspecification': {
            'Meta': {'object_name': 'TestSpecification'},
            'description': ('jsonfield.fields.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['greenfan']
