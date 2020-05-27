.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. http://creativecommons.org/licenses/by/4.0

Developer Guide
===============

.. contents::
   :depth: 3
   :local:

Tech Stack
----------

The A1 Mediator is implemented in Python, currently version 3.8, and
depends on these third-party packages and technologies:

- OpenAPI3
- Connexion
- Flask with Gevent serving
- Swagger

Version bumping A1
------------------

This project follows semver. When the version string changes, these
files must be updated:

#. ``setup.py``
#. ``container-tag.yaml``
#. ``integration_tests/a1mediator/Chart.yaml``
#. ``docs/release-notes.rst``
#. ``a1/openapi.yaml`` But note this is an API version, not a software version; there's no need to bump on non-API changes.
#.  And over in the ric-plt/ric-dep repo that contains the A1 Mediator helm chart, files ``values.yaml`` and ``Chart.yaml``.

It's convenient to use the Python utility `bumpversion` to maintain
the first three items.  After setup (``pip install bumpversion``) you
can change the patch version like this::

    bumpversion --verbose patch

Or change the minor version like this::

    bumpversion --verbose minor

After the `bumpversion` utility has modified the files, update the
release notes then commit.


Version bumping RMR
-------------------

A1 (Dockerfile), Dockerfile-Unit-Test, and all three integration test
receivers use an Alpine base image and install RMR from a base builder
image.  Must update and rebuild all 5 containers in the A1 repo (or
just A1 itself for production usage).

In addition these items in this repo must be kept in sync:

#. ``rmr-version.yaml`` controls what rmr gets installed for unit
   testing in Jenkins
#. ``integration_tests/install_rmr.sh`` is a useful script for a
   variety of local testing.

Version bumping Python
----------------------

If you want to update the version of python; for example this was
recently done to move from 3.7 to 3.8, update these files:

#. ``Dockerfile``
#. ``Dockerfile-Unit-Test``
#. ``tox.ini``

Unit Testing
------------

Running the unit tests requires the python packages ``tox`` and ``pytest``.

The RMR library is also required during unit tests. If running
directly from tox (outside a Docker container), install RMR using the
script in the integration_tests directory: ``install_rmr.sh``.

Upon completion, view the test coverage like this:

::

   tox
   open htmlcov/index.html

Alternatively, you can run the unit tests in Docker (this is somewhat
less nice because you don't get the pretty HTML)

::

   docker build  --no-cache -f Dockerfile-Unit-Test .

Integration testing
-------------------

This tests A1’s external API with three test receivers. This requires
docker, kubernetes and helm.

Build all the images:

::

    docker build  -t a1:latest .
    cd integration_tests/testxappcode
    docker build -t delayreceiver:latest -f Dockerfile-delay-receiver .
    docker build -t queryreceiver:latest -f Dockerfile-query-receiver .
    docker build -t testreceiver:latest  -f Dockerfile-test-receiver  .


Then, run all the tests from the root (this requires the python packages ``tox``, ``pytest``, and ``tavern``).

::

   tox -c tox-integration.ini

This script:

#. Deploys 3 helm charts (5 containers) into a local kubernetes installation
#. Port forwards a pod ClusterIP to localhost
#. Uses “tavern” to run some tests against the server
#. Barrages the server with Apache bench
#. Tears everything down
