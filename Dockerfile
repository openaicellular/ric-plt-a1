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
# TODO: switch to alpine once rmr apk available
FROM python:3.7

COPY . /tmp
WORKDIR /tmp

# copy NNG out of the  CI builder nng
COPY --from=nexus3.o-ran-sc.org:10004/bldr-debian-python-nng:2-py3.7-nng1.1.1 /usr/local/lib/libnng.so /usr/local/lib/libnng.so

# Installs RMr using debian package hosted at packagecloud.io
RUN wget --content-disposition https://packagecloud.io/o-ran-sc/master/packages/debian/stretch/rmr_1.0.36_amd64.deb/download.deb
RUN dpkg -i rmr_1.0.36_amd64.deb

# dir that rmr routing file temp goes into
RUN mkdir -p /opt/route/

# Install RMr python bindings
# this writes into /usr/local, need root
RUN pip install --upgrade pip && pip install rmr==0.10.1 tox

# Run the unit tests
RUN tox

# do the actual install
RUN pip install .

# Switch to a non-root user for security reasons.
# a1 does not currently write into any dirs so no chowns are needed at this time.
# https://stackoverflow.com/questions/27701930/add-user-to-docker-container
RUN adduser --disabled-password --gecos '' a1user
USER a1user

# misc setups
EXPOSE 10000
ENV LD_LIBRARY_PATH /usr/local/lib
ENV RMR_SEED_RT /opt/route/local.rt

CMD run.py
