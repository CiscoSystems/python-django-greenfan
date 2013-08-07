Jobs
====

Greenfan runs jobs that can be created in a couple of different ways (FIXME:
what are they?). Jobs are either considered "physical" or "virtual" depending
on whether they are to be run on physical nodes or on top of OpenStack. At some
point, the ability to run physical tests will probably be restricted to a
limited set of users, since physical resources are much more prone to
starvation.

Jobs have a description, typically passed around in the shape of a JSON object:

These are the available keys in the JSON object:

.. _jobspec-tenants:

``tenants``
   holds an array of tenant that are to be provisioned once the deployment is
   completed, but before images are added and Tempest is run.
    
   Each element in the ``tenants`` array is an object with the following keys:

   ``name``
      The name of the tenant (mandatory)

   ``description``
      The tenant's description (defaults to `<name>`) 

.. _jobspec-users:

``users``
   holds an array of users that are to be provisioned once the deployment is
   completed, but before images are added and Tempest is run.

   Each element in the `users` array is an object with the following keys:

   ``tenant``
      The name of the user's primary tenant (mandatory)
 
   ``name``
      The user's own name (mandatory)

   ``password``
      The password to set for the user (mandatory)

   ``email``
      The e-mail of the user (defaults to <username>@example.com)

   ``roles``
      An array of role names that user will be assigned under the given tenant (default to [])

.. _jobspec-images:

``images``
   holds an array of images that are to be added to the deployment before
   tempest is run

   Each element in the `images` array is an object with the following keys:

   ``name``
      The name to assign to the image (mandatory)

   ``container``_``format``
      The container format of the image (mandatory)

   ``disk``-``format``
      The disk format of the image (mandatory)

   ``url``
      The URL where we can load the image from (mandatory)


``manifest``
   an object describing how to construct the Puppet manifests

   The following keys are available:

   ``content``
      If specified, will be stored in `site.pp` on the Puppet master
      and no further manifest construction will be performed

   ``git``
      An object describing how to construct the Puppet manifests from
      git. The following keys are available:

      ``repository``
         The URL of the repository holding (templates for) the manifest.
         (mandatory)

      ``subdir``
         The subdirectory in the git branch that is the root of the
         directory hierarchy that we care about.

      ``branch``
         The branch to pull from the repository

   ``destdir``
      The destination directory for the generated manifest(s). (defaults to
      /etc/puppet/manifests) 

.. _jobspec-archives:

``archives``
   holds an array of objects describing the package sources for the test

   Each element of the `archives` array is an object with the following keys:
   
   ``line``
      A sources.list line (in a form that can be consumed by
      add-apt-repository as a single argument) (mandatory)

   ``key_data``
      The signing key for the given repository in a format consumable by
      "apt-key add" (either this or key_id must be given)

   ``key_id``
      The key_id of the signing key for the given repository (will be
      fetched from keyserver.ubuntu.com). (either this or key_data must be
      given)
          
   ``proxy``
      A proxy to use for this repository


.. _jobspec-nodes:

``nodes``
   an object describing which nodes the test should be run on

   The following keys are available:

   ``include``
      a string or an array of strings. Each string should be a hardware
      tag. If specified, only nodes matching one of these tags will be
      considered for this job.

   ``exclude``
      a string or array of strings. Each string should be a hardware tag.
      If specified, nodes matching one of these tags will not be
      considered for this job.

``num_nodes``
   An integer specifying how many nodes to use for this job. Defaults to 3.


You can add your own keys if you need extra data passed into the
manifest generation process.

