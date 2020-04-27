.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0
.. Copyright (C) 2019 AT&T Intellectual Property

A1 Installation Guide
=====================

.. contents::
   :depth: 3
   :local:

Optional ENV Variables
----------------------

You can set the following ENVs to change the A1 behavior:

1. ``A1_RMR_RETRY_TIMES``: the number of times failed rmr operations such as timeouts and send failures should be retried before A1 gives up and returns a 503. The default is ``4``.

2. ``INSTANCE_DELETE_NO_RESP_TTL``: Please refer to the delete flowchart in docs/; this is ``T1`` there. The default is 5 (seconds). Basically, the number of seconds that a1 waits to remove an instance from the database after a delete is called in the case that no downstream apps responded.

3. ``INSTANCE_DELETE_RESP_TTL``: Please refer to the delete flowchart in docs/; this is ``T2`` there. The default is 5 (seconds). Basically, the number of seconds that a1 waits to remove an instance from the database after a delete is called in the case that downstream apps responded.

K8S
---
The "real" helm chart for A1 is in the LF it/dep repo. That repo holds all of the helm charts for the RIC platform. There is a helm chart in `integration_tests` here for running the integration tests as discussed above.

Local Docker
-------------

building
~~~~~~~~
::

   docker build --no-cache -t a1:X.Y.Z .

.. _running-1:

running
~~~~~~~

::

   docker run -dt -p 10000:10000 -v /path/to/localrt:/opt/route/local.rt -v /path/to/ricmanifest:/opt/ricmanifest.json a1:X.Y.Z -v

