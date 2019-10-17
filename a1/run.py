"""
A1 entrypoint
"""
# ==================================================================================
#       Copyright (c) 2019 Nokia
#       Copyright (c) 2018-2019 AT&T Intellectual Property.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ==================================================================================
import time
from threading import Thread
from gevent.pywsgi import WSGIServer
from a1 import get_module_logger, app
from a1 import a1rmr


logger = get_module_logger(__name__)


def start_rmr_thread(real_init=True):
    """
    Start a1s rmr thread
    Also called during unit testing
    """
    rmr_loop = a1rmr.RmrLoop(real_init)
    thread = Thread(target=rmr_loop.loop)
    thread.start()
    while not rmr_loop.rmr_is_ready():
        time.sleep(0.5)
    return rmr_loop  # return the handle; useful during unit testing


def main():
    """Entrypoint"""
    # start rmr thread
    logger.debug("Initializing rmr thread. A1s webserver will not start until rmr initialization is complete.")
    start_rmr_thread()

    # start webserver
    logger.debug("Starting gevent server")
    http_server = WSGIServer(("", 10000), app)
    http_server.serve_forever()
