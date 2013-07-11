# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Job.step'
        db.alter_column(u'greenfan_job', 'step', self.gf('django.db.models.fields.IntegerField')(null=True))

    def backwards(self, orm):

        # Changing field 'Job.step'
        db.alter_column(u'greenfan_job', 'step', self.gf('django.db.models.fields.CharField')(max_length=40, null=True))

    models = {
        u'cloudslave.cloud': {
            'Meta': {'object_name': 'Cloud'},
            'endpoint': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'flavor_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'floating_ip_mode': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'image_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'tenant_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'user_name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        u'cloudslave.reservation': {
            'Meta': {'object_name': 'Reservation'},
            'cloud': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloudslave.Cloud']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number_of_slaves': ('django.db.models.fields.IntegerField', [], {}),
            'state': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'timeout': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'greenfan.configuration': {
            'Meta': {'object_name': 'Configuration'},
            'admin_password': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'admin_user': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'gateway': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nameservers': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'netmask': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'ntp_servers': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'proxy': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'subnet': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'})
        },
        u'greenfan.hardwareprofile': {
            'Meta': {'object_name': 'HardwareProfile'},
            'description': ('jsonfield.fields.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['greenfan.HardwareProfileTag']", 'symmetrical': 'False'})
        },
        u'greenfan.hardwareprofiletag': {
            'Meta': {'object_name': 'HardwareProfileTag'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'})
        },
        u'greenfan.job': {
            'Meta': {'object_name': 'Job'},
            'cloud_slave_reservation': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cloudslave.Reservation']", 'null': 'True', 'blank': 'True'}),
            'description': ('jsonfield.fields.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'log_listener_port': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'physical': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'step': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'greenfan.server': {
            'Meta': {'object_name': 'Server'},
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hardware_profile': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['greenfan.HardwareProfile']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'job': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['greenfan.Job']", 'null': 'True', 'blank': 'True'}),
            'mac': ('django.db.models.fields.CharField', [], {'max_length': '17'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'power_address': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'power_id': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'power_password': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'power_type': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'power_user': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        u'greenfan.testspecification': {
            'Meta': {'object_name': 'TestSpecification'},
            'description': ('jsonfield.fields.JSONField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['greenfan']