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

A1 Mediator Release Notes
=========================

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <http://keepachangelog.com/>`__
and this project adheres to `Semantic
Versioning <http://semver.org/>`__.

[0.8.3] - 6/18/2019
-------------------

::

   * Use base Docker with NNG version 1.1.1



[0.8.2] - 6/5/2019
-------------------

::

   * Upgrade RMR due to a bug that was preventing rmr from init in kubernetes



[0.8.1] - 5/31/2019
-------------------

::

   * Run unit tests as part of docker build



[0.8.0] - 5/28/2019
-------------------

::

   * Convert docs to appropriate format
   * Move rmr string to int mapping to a file



[0.7.2] - 5/24/2019
-------------------

::

   * Use tavern to test the actual running docker container
   * Restructures the integration tests to run as a single tox command
   * Re-ogranizes the README and splits out the Developers guide, which is not needed by users.

.. _section-1:

[0.7.1] - 5/23/2019
-------------------

::

   * Adds a defense mechanism against A1 getting queue-overflowed with messages A1 doesnt care about; A1 now ignores all incoming messages it's not waiting for, so it's queue size should now always be "tiny", i.e., never exceeding the number of valid requests it's waiting for ACKs back for
   * Adds a test "bombarding" script that tests this

.. _section-2:

[0.7.0] - 5/22/19
-----------------

::

   * Main purpose of this change is to fix a potential race condition where A1 sends out M1 expecting ACK1, and while waiting for ACK1, sends out M2 expecting ACK2, but gets back ACK2, ACK1. Prior to this change, A1 may have eaten ACK2 and never fufilled the ACK1 request.
   * Fix a bug in the unit tests (found using a fresh container with no RIC manifest!)
   * Fix a (critical) bug in a1rmr due to a rename in the last iteration (RMR_ERR_RMR_RCV_RETRY_INTERVAL)
   * Make unit tests faster by setting envs in tox
   * Move to the now publically available rmr-python
   * Return a 400 if am xapp does not expect a body, but the PUT provides one
   * Adds a new test policy to the example RIC manifest and a new delayed receiver to test the aformentiond race condition

.. _section-3:

[0.6.0]
-------

::

   * Upgrade to rmr 0.10.0
   * Fix bad api spec RE GET
   * Fix a (big) bug where transactionid wasn't being checked, which wouldn't have worked on sending two policies to the same downstream policy handler

.. _section-4:

[0.5.1] - 5/13/2019
-------------------

::

   * Rip some testing structures out of here that should have been in rmr (those are now in rmr 0.9.0, upgrade to that)
   * Run Python BLACK for formatting

.. _section-5:

[0.5.0] - 5/10/2019
-------------------

::

   * Fix a blocking execution bug by moving from rmr's timeout to a non blocking call + retry loop + asyncronous sleep
   * Changes the ENV RMR_RCV_TIMEOUT to RMR_RCV_RETRY_INTERVAL

.. _section-6:

[0.4.0] - 5/9.2019
------------------

::

   * Update to rmr 0.8.3
   * Change 503 to 504 for the case where downstream does not reply, per recommendation
   * Add a 502 with different reasons if the xapp replies but with a bad/malformed/missing status
   * Make testing much more modular, in anticipating of moving some unit test functionality into rmr itself

.. _section-7:

[0.3.4] - 5/8/2019
------------------

::

   * Crash immediately if manifest isn't mounted
   * Add unit tests for utils
   * Add missing lic

.. _section-8:

[0.3.3]
-------

::

   * Upgrade A1 to rmr 0.8.0
   * Go from deb RMR installation to git
   * Remove obnoxious receiver logging

.. _section-9:

[0.3.2]
-------

::

   * Upgrade A1 to rmr 0.6.0

.. _section-10:

[0.3.1]
-------

::

   * Add license headers

.. _section-11:

[0.3.0]
-------

::

   * Introduce RIC Manifest
   * Move some testing functionality into a helper module
   * Read the policyname to rmr type mapping from manifest
   * Do PUT payload validation based on the manifest

.. _section-12:

[0.2.0]
-------

::

   * Bump rmr python dep version
   * Include a Dockerized test receiver
   * Stencil out the mising GET
   * Update the OpenAPI
   * Include a test docker compose file

.. _section-13:

[0.1.0]
-------

::

   * Initial Implementation
