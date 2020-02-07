.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

Developer-Guide
===============

.. contents::
   :depth: 3
   :local:

Tech Stack
----------

-  OpenAPI3
-  Connexion
-  Flask with Gevent serving
-  Python3.7

Version bumping
---------------

This project follows semver. When changes are made, the versions are in:

1) ``docs/release-notes.rst``

2) ``setup.py``

3) ``container-tag.yaml``

4) ``integration_tests/a1mediator/Chart.yaml``

6) ``a1/openapi.yaml`` (this is an API version, not a software version; no need to bump on patch changes)

7) in the it/dep repo that contains a1 helm chart, ``values.yaml``, ``Chart.yml``


Version bumping rmr
-------------------
As of 2020/02/13, A1 and all three integration test receivers use a base image from o-ran-sc.
The rmr version is in that base image.
However, the one item in this repo that must be kept in sync is ``rmr-version.yaml``. This controls what rmr gets installed for unit testing.

Version bumping pyrmr
---------------------
rmr-python is the python binding to rmr . Installing rmr per the above does not install it.
Bumping the rmr python version dependency requires changes in:

1) ``setup.py``

2) ``integration_tests/Dockerfile-test-delay-receiver``

3) ``integration_tests/Dockerfile-query-receiver``

Run the integration tests after attempting this.

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
1. Deploys 2 helm charts (4 containers) into a local kubernetes installation
2. Port forwards a pod ClusterIP to localhost
3. Uses “tavern” to run some tests against the server
4. Barrages the server with apache bench
5. Tears everything down
