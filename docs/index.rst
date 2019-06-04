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

Unit Testing
============

Note, this requires rmr to be installed!

::

   tox
   open htmlcov/index.html

Integration testing
===================

This tests A1’s external API with two test receivers. Note, this
currently depends on docker-compose, meaning you cannot run this if
docker-compose is not installed. Note2: this is not fast. It builds the
containers and launches requests against the API so it takes time.

::

   tox -c tox-integration.ini

Running
=======

Optional ENV Variables
----------------------

You can set the following ENVs to change the A1 behavior: 1)
``RMR_RCV_RETRY_INTERVAL`` the number of milliseconds that execution
will defer (back to the server loop to handle http request if
applicable) when an expected ack is not received by rmr call. The
default is ``1000`` (1s). The time for the full HTTP request to
``PUT /policies`` will be > this if an ACK is not recieved within 10ms,
which is an initial delay until the first rcv is tried. 2)
``RMR_RETRY_TIMES`` the number of times failed rmr operations such as
timeouts and send failures should be retried before A1 gives up and
returns a 503. The default is ``4``.

K8S
---
The helm chart is in the folder `a1mediator`.

There are two files in `a1mediator/files` that should be replaced with the "real" files for deployment. The ones included there, and referenced in the configmap, are only samples. To deploy A1 correctly, make sure these files are correct.

::

    helm install --devel a1mediator/ --name a1 --set imageCredentials.username=xxx --set imageCredentials.password=xxx

The username and password here are the credentials to the registry defined in `a1mediator/values.yaml`. Currently this is the LF docker registry.

Docker
------

building
~~~~~~~~

::

   docker build --no-cache -t a1:X.Y.Z .

.. _running-1:

running
~~~~~~~

(TODO: this will be enhanced with Helm.)

::

   docker run -dt -p 10000:10000 -v /path/to/localrt:/opt/route/local.rt -v /path/to/ricmanifest:/opt/ricmanifest.json a1:X.Y.Z -v
