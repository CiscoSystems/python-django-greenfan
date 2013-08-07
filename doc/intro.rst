============
Introduction
============

Greenfan's job is to verify the functionality of the Cisco OpenStack Edition
(COE).

Whatever COE's documentation tells the user to do, Greenfan attempts to
imitate. This involves:

 * provisioning physical or virtual machines,
 * installing and configurating an operating system,
 * installing and configurating Puppet,
 * installing Puppet modules,
 * constructing manifests,
 * etc.

See :doc:`steps` for more detail.

Greenfan's database has a table of nodes that are available for testing. It
details the hostnames, mac addresses, UCSM identifiers, etc. Each node has a
defined hardware profile. Each hardware profile has a number of tags. These
tags serve as a mechanism for filtering nodes to be used for tests. Tags could
be ``1-nic``, ``2-nic``, ``blade``, ``rack``, etc. See :ref:`the filtering docs
(jobspec.nodes) <jobspec-nodes>` for more info.

The database also holds a number of test specifications. Test specifications
are job templates. They're useful if the same test is supposed to be run over
and over and over.

The intent is for Greenfan to offer an API that lets things like Jenkins submit
a job. So far, Jenkins can call Greenfan through its command line interface
(creating jobs based on a test spec).

It's definitely worth pointing out that Greenfan's methodology is not meant to
endorse any or all of the design decisions of COE. Greenfan came into existence
to fill a void: There was no automatic end-to-end testing of COE. It's
important to be encouraged to revise the installation methodology employed by
COE without regard for Greenfan. COE should dictate Greenfan's functionality,
not the other way around.


