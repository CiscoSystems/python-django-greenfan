# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Job'
        db.create_table('greenfan_job', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('jsonfield.fields.JSONField')(default={})),
            ('log_listener_port', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('state', self.gf('django.db.models.fields.SmallIntegerField')(default=1)),
        ))
        db.send_create_signal('greenfan', ['Job'])

        # Deleting field 'TestSpecification.log_listener_port'
        db.delete_column('greenfan_testspecification', 'log_listener_port')

        # Deleting field 'TestSpecification.log_listener_dir'
        db.delete_column('greenfan_testspecification', 'log_listener_dir')


    def backwards(self, orm):
        # Deleting model 'Job'
        db.delete_table('greenfan_job')

        # Adding field 'TestSpecification.log_listener_port'
        db.add_column('greenfan_testspecification', 'log_listener_port',
                      self.gf('django.db.models.fields.IntegerField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'TestSpecification.log_listener_dir'
        db.add_column('greenfan_testspecification', 'log_listener_dir',
                      self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True),
                      keep_default=False)


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
            'description': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['greenfan.HardwareProfileTag']", 'symmetrical': 'False'})
        },
        'greenfan.hardwareprofiletag': {
            'Meta': {'object_name': 'HardwareProfileTag'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'})
        },
        'greenfan.job': {
            'Meta': {'object_name': 'Job'},
            'description': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log_listener_port': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'})
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
            'description': ('jsonfield.fields.JSONField', [], {'default': '{}'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['greenfan']