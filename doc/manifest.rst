.. _manifest-generation:

===================
Manifest generation
===================

Every file in the git branch (under the given subdir) is run through
Django's template processor. The following context variables are
available to the templating engine:

``job``
   The job being run.

   ``job.description``
      the job description passed in per above.

  ``job.build_node``
     is a Node object representing the build node.

  ``job.controller_node``
     is a Node object representing the controller.

``config``
   Some general configration things:

   ``config.nameservers``
      space separated list of name servers

   ``config.ntp_servers``
     space separated list of NTP servers

   ``config.admin_user``
     Desired username for administrative user

   ``config.admin_password``
     Desired password for administratvive user

   ``config.proxy``
     Proxy to use across the board

   ``config.domain``
     The domain name to use for all nodes and services

``nodes``
   The nodes used in the deployment

   They have the following attributes:

   ``node.mac``
      Node's primary NIC's MAC address

   ``node.subnet``
      Node's primary interface's subnet

   ``node.subnet_as_sql``
      An attempt to render a subnet as something suitable for an
      SELECT ... LIKE statement. E.g. 10.0.0.0/24 becomes '10.0.0.%',
      10.0.0.0/16 becomes '10.0.%.%'. It errs on the side of ensuring things
      can reach each other, so 10.0.0.0/20 becomes '10.0.0.%'.

   ``node.netmask``
      Node's primary interface's netmask

   ``node.gateway``
      Node's primary interface's gateway

   ``node.power_address``
      The address of the power management API

   ``node.power_type``
      The power type of the instance (either 'ucs' or 'ipmi')

   ``node.power_user``
      User to authenticate against power mgmt API as

   ``node.power_password``
      Password to use to to authenticate against power mgmt API

   ``node.power_id``
      The ID in the power mgmt API of this node (may not be needed depending
      on power type)

   ``node.internal_ip``
      IP that the node is known as to its neighbours

   ``node.external_ip``
      IP that the node can be reached at from the Greenfan host

   ``node.name``
      Name of the node

   ``node.fqdn``
      FQDN of the node
