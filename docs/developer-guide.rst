.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

A1 Developer Guide
==================

.. contents::
   :depth: 3
   :local:

Tech Stack
----------

-  OpenAPI3
-  Connexion
-  Flask with Gevent serving
-  Python3.8

Version bumping A1
------------------

This project follows semver. When changes are made, the versions are in:

1) ``docs/release-notes.rst``

2) ``setup.py``

3) ``container-tag.yaml``

4) ``integration_tests/a1mediator/Chart.yaml``

5) ``a1/openapi.yaml`` (this is an API version, not a software version; no need to bump on patch changes)

6) in the ric-plt repo that contains a1 helm chart, ``values.yaml``, ``Chart.yml``


Version bumping RMR
-------------------

As of 2020/02/13, A1 (Dockerfile), Dockerfile-Unit-Test,  and all three integration test receivers use a base image from o-ran-sc.
The rmr version is in that base image.
When version changes are made in that image, rebuilding those 5 containers in the A1 repo will pick it up (or just A1 itself for prod usage).

However, there are two items in this repo that must be kept in sync:  ``rmr-version.yaml``, which  controls what rmr gets installed for unit testing in Jenkins, and ``integration_tests/install_rmr.sh`` which is a useful script for a variety of local testing.

Version bumping Python
----------------------

If you want to update the version of python itself (ie just done from 37 to 38):

1) ``Dockerfile``

2) ``Dockerfile-Unit-Test``

3) ``tox.ini``

Unit Testing
------------

Note,  before this will work, for the first time on the machine running the tests, run ``./install_deps.sh``. This is only needed once on the machine.
Also, this requires the python packages ``tox`` and ``pytest``.

::

   tox
   open htmlcov/index.html

Alternatively, you can run the unit tests in Docker (this is somewhat less nice because you don't get the pretty HTML)

::

   docker build  --no-cache -t a1test:latest -f Dockerfile-Unit-Test

Integration testing
-------------------

This tests A1’s external API with three test receivers. This depends on helm+k8s.

Build all the containers:

::

    docker build  -t a1:latest .; cd integration_tests/; docker build  -t testreceiver:latest . -f Dockerfile-test-delay-receiver; docker build -t queryreceiver:latest . -f Dockerfile-query-receiver; cd ..


Then, run all the tests from the root (this requires the python packages ``tox``, ``pytest``, and ``tavern``).

::

   tox -c tox-integration.ini

This script:
1. Deploys 3 helm charts (5 containers) into a local kubernetes installation
2. Port forwards a pod ClusterIP to localhost
3. Uses “tavern” to run some tests against the server
4. Barrages the server with apache bench
5. Tears everything down
