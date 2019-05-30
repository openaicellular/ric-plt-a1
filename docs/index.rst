A1
==

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
