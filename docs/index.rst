.. ==================================================================================
..       Copyright (c) 2019 Nokia
..       Copyright (c) 2018-2019 AT&T Intellectual Property.
..
..   Licensed under the Apache License, Version 2.0 (the "License");
..   you may not use this file except in compliance with the License.
..   You may obtain a copy of the License at
..
..          http://www.apache.org/licenses/LICENSE-2.0
..
..   Unless required by applicable law or agreed to in writing, software
..   distributed under the License is distributed on an "AS IS" BASIS,
..   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
..   See the License for the specific language governing permissions and
..   limitations under the License.
.. ==================================================================================

A1 Mediator
===========

API
===

You can see the API (OpenAPI3 spec) at ``a1/openapi.yml``. You can also
see the “pretty” version if you run the container at
``http://localhost:10000/ui/``.

Running
=======

Optional ENV Variables
----------------------

You can set the following ENVs to change the A1 behavior:

1. ``RMR_RETRY_TIMES`` the number of times failed rmr operations such as
timeouts and send failures should be retried before A1 gives up and
returns a 503. The default is ``4``.

K8S
---
The "real" helm chart for A1 is in the LF it/dep repo. That repo holds all of the helm charts for the RIC platform. There is a helm chart in `integration_tests` here for running the integration tests as discussed above.

Local Docker
------------

building
~~~~~~~~
::

   docker build --no-cache -t a1:X.Y.Z .

.. _running-1:

running
~~~~~~~

::

   docker run -dt -p 10000:10000 -v /path/to/localrt:/opt/route/local.rt -v /path/to/ricmanifest:/opt/ricmanifest.json a1:X.Y.Z -v
