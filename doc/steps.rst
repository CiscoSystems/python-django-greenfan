.. Stuff:

=====
Steps
=====

 * :ref:`Start log listener <start-log-listener>`
 * :ref:`reserve-nodes`
 * :ref:`list-nodes`
 * :ref:`provision-build-node`
 * :ref:`wait-for-build-node`
 * :ref:`install-and-configure-puppet`
 * :ref:`reboot-non-build-node`
 * :ref:`wait-for-non-build-nodes`
 * :ref:`provision-users`
 * :ref:`import-images`
 * :ref:`run-tempest`
 * :ref:`stop-log-listener`
 * :ref:`turn-off-non-build-nodes`
 * :ref:`release-nodes`


.. _start-log-listener:

Start log listener
------------------

Each build has a log listener of its own.

The start-log-listener step scans through the output of ``netstat -lun`` to find
an available UDP port. Once it finds one, it generates an rsyslog config file
and invokes rsyslog. The port number is stored in the database. Everything else
is stored in the job log directory.


.. _reserve-nodes:

Reserve nodes
-------------

Reserves a number of nodes for the test run.

In the case of virtual jobs, the relevant number of VM's (3, by default) are started at this step.

For physical jobs, the scheduler will look at the current pool of hardware and use the "include" and "exclude" specifications from the job to pick the nodes for this job. See :ref:`jobspec.nodes <jobspec-nodes>` for more information.

.. _list-nodes:

List nodes
----------

Outputs a list of nodes, as well as some other information about the current job.

.. _provision-build-node:

Provision build node
--------------------

Provisions the build node.

In the case of virtual jobs, this is a no-op as all VM's have been provisioned in the :ref:`reserve-nodes` step.

In the case of physical jobs, this is done by
 * creating a preseed file (based on :download:`../greenfan/templates/build-node.preseed.tmpl`),
 * adding the designated build node to a local Cobbler instance (by issuing cobbler CLI commands),
 * rebooting the build node.

.. _wait-for-build-node:

Wait for build node
-------------------

Waits for the build node to be ready by continuously attempting to log in over SSH and running the command ``true``.

.. _install-and-configure-puppet:

Install and configure puppet
----------------------------

 * :ref:`Generates the manifests <manifest-generation>` and copies them to the build node.
 * Configures the :ref:`archives specified in the job spec <jobspec-archives>` used for installation of puppet modules.
 * Installs ``openssh-server``, ``puppetmaster-passenger``, ``puppet``, and ``puppet-openstack-cisco``
 * Calls ``puppet apply /etc/puppet/manifests/site.pp``
 * Calls ``puppet agent -t || true`` (IIRC, this is to ensure all SSL certs are generated)
 * Makes sure ``-z`` is added to the command line in ``/etc/cobbler/power/power_ucs.template`` since ssl was suddenly required to speak to some of the UCSMs.

.. _reboot-non-build-node:

Reboot non build nodes
----------------------

Upon completion of :ref:`install-and-configure-puppet`, all the non-build should be configured in the build node's Cobbler instance.

For physical jobs, Greenfan calls upon cobbler to reboot them.

For virtual jobs, Greenfan logs into each of them, installs the ``pxe-kexec`` package and invokes ``pxe-exec -n -l linux -i eth0 {internal IP of build node}``. This is supposed to be functionally equivalent of PXE booting, which isn't generally possible in an OpenStack cloud (yet).

.. _wait-for-non-build-nodes:

Wait for non-build nodes
------------------------

To determine whether all the build nodes have finished installing, Greenfan continuously checks for reports in ``/var/lib/puppet/reports`` on the build node. This indicates that they've finished their first Puppet run.

.. _provision-users:

Provision users
---------------

Greenfan provisions the users as specified in :ref:`jobspec.tenants <jobspec-tenants>` and :ref:`jobspec.users <jobspec-users>`.

Note: The keystone admin token is hardcoded in Greenfan as "``keystone_admin_token``", so make sure that's how the deployment configures it.

.. _import-images:

Import images
-------------

Greenfan install images (as per :ref:`jobspec.images <jobspec-images>`) by running ``glance`` CLI commands on the controller node. If this CLI interface changes, we're in trouble.

.. _run-tempest:

Run tempest
-----------

There's a comment in :download:`../greenfan/management/commands/run-tempest.py` that sums it all up pretty well:

    This is crude and horrible.

First of all, the git url and branch are hardcoded. Obviously, this should be specified in the job spec, but right now, the ``stable/folsom`` branch of ``https://github.com/CiscoSystems/tempest`` is used.


It turns out that the order of the users configured in the job specification is very important. The user listed first is assumed to have administrative privileges. The second and third (woe is he who does not specify at least three users) are non-privileged users.

Greenfan goes through etc/tempest.conf.sample and replaces a bunch of the values:

In the ``identity-admin`` and ``compute-admin`` sections:

``username``
    replaced with the name of the administrative user

``tenant_name``
    replace with the tenant name of the administrative user

``password``
    replace with the password of the administrative user


In all other sections:

``username``
    replaced with the name of the first, non-privileged user

``tenant_name``
    replace with the tenant name of the first, non-privileged user

``password``
    replace with the password of the first, non-privileged user

In all sections:

``alt_username``
    replaced with the name of the second, non-privileged user

``alt_tenant_name``
    replace with the tenant name of the second, non-privileged user

``alt_password``
    replace with the password of the second, non-privileged user

``image_ref``
    replace with the image id of the image loaded during :ref:`import-images`

``image_ref``
    replace with the image id of the image loaded during :ref:`import-images` (yes, same as image_ref)

In the ``compute`` section:

``create_image_enabled``
    set to false
    
``resize_available``
    set to false
    
``change_password_available``
    set to false
    
``whitebox_enabled``
    set to false
    
In the ``network`` section:

``api_version``
    set to "v2.0"
    

Once this tempest configuration has been written, Greenfan installs ``git``, ``python-unittest2``, ``python-testtools``, and ``python-testresources``.

Finally, Greenfan runs ``nosetests -v -a '!whitebox' tempest`` from within the tempest directory.


.. _stop-log-listener:

Stop log listener
-----------------

Stops the log listener started in :ref:`start-log-listener`.

.. _turn-off-non-build-nodes:

Turn off non build nodes
------------------------

Turn off non-build nodes. This is done to prevent them from continuing to send out syslog information which can be very confusing if a log listener starts on the same port for a later test run.

For physical jobs, Greenfan calls upon Cobbler on the build node to power them off.

For virtual jobs, this step doesn't actually do anything.

.. _release-nodes:

Release nodes
-------------

Unreserves nodes, putting them back into the pool of available resources.

For physical jobs, this unlinks the nodes from the job (a simple db operation).

For virtual jobs, it destroys all the cloud instances that have been used in the job.
