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
        # Adding model 'TestSpecification'
        db.create_table('greenfan_testspecification', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('jsonfield.fields.JSONField')()),
        ))
        db.send_create_signal('greenfan', ['TestSpecification'])

        # Adding model 'Configuration'
        db.create_table('greenfan_configuration', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('subnet', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('netmask', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('gateway', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('ntp_servers', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('nameservers', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('proxy', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('greenfan', ['Configuration'])

        # Adding model 'HardwareProfileTag'
        db.create_table('greenfan_hardwareprofiletag', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200, primary_key=True)),
        ))
        db.send_create_signal('greenfan', ['HardwareProfileTag'])

        # Adding model 'HardwareProfile'
        db.create_table('greenfan_hardwareprofile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('description', self.gf('jsonfield.fields.JSONField')()),
        ))
        db.send_create_signal('greenfan', ['HardwareProfile'])

        # Adding M2M table for field tags on 'HardwareProfile'
        db.create_table('greenfan_hardwareprofile_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('hardwareprofile', models.ForeignKey(orm['greenfan.hardwareprofile'], null=False)),
            ('hardwareprofiletag', models.ForeignKey(orm['greenfan.hardwareprofiletag'], null=False))
        ))
        db.create_unique('greenfan_hardwareprofile_tags', ['hardwareprofile_id', 'hardwareprofiletag_id'])

        # Adding model 'Server'
        db.create_table('greenfan_server', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('mac', self.gf('django.db.models.fields.CharField')(max_length=17)),
            ('power_address', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('power_type', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('power_user', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('power_password', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('power_id', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('hardware_profile', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['greenfan.HardwareProfile'])),
        ))
        db.send_create_signal('greenfan', ['Server'])


    def backwards(self, orm):
        # Deleting model 'TestSpecification'
        db.delete_table('greenfan_testspecification')

        # Deleting model 'Configuration'
        db.delete_table('greenfan_configuration')

        # Deleting model 'HardwareProfileTag'
        db.delete_table('greenfan_hardwareprofiletag')

        # Deleting model 'HardwareProfile'
        db.delete_table('greenfan_hardwareprofile')

        # Removing M2M table for field tags on 'HardwareProfile'
        db.delete_table('greenfan_hardwareprofile_tags')

        # Deleting model 'Server'
        db.delete_table('greenfan_server')


    models = {
        'greenfan.configuration': {
            'Meta': {'object_name': 'Configuration'},
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
