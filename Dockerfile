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
# install a well known working rmr
FROM python:3.7-alpine
RUN apk update && apk add autoconf automake build-base cmake libtool ninja pkgconfig git
RUN git clone --branch 1.8.1 https://gerrit.o-ran-sc.org/r/ric-plt/lib/rmr \
    && cd rmr \
    && mkdir build \
    && cd build \
    && cmake .. -DPACK_EXTERNALS=1 \
    && make install

# a1 stage 2
FROM python:3.7-alpine

# copies
COPY --from=0 /usr/local/lib64/libnng.so /usr/local/lib64/libnng.so
COPY --from=0 /usr/local/lib64/librmr_nng.so /usr/local/lib64/librmr_nng.so
COPY a1/ /tmp/a1
COPY tests/ /tmp/tests
COPY setup.py tox.ini /tmp/
WORKDIR /tmp

# dir that rmr routing file temp goes into
RUN mkdir -p /opt/route/

# Gevent needs gcc
RUN apk update && apk add bash gcc musl-dev

# do the actual install; this writes into /usr/local, need root
RUN pip install --upgrade pip && pip install .

# Switch to a non-root user for security reasons.
# a1 does not currently write into any dirs so no chowns are needed at this time.
ENV A1USER a1user
RUN addgroup -S $A1USER && adduser -S -G $A1USER $A1USER 
USER $A1USER

# misc setups
EXPOSE 10000
ENV LD_LIBRARY_PATH /usr/local/lib/:/usr/local/lib64
ENV RMR_SEED_RT /opt/route/local.rt

# dont buffer logging
ENV PYTHONUNBUFFERED 1

CMD run.py
