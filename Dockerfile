# ==================================================================================
#       Copyright (c) 2019-2020 Nokia
#       Copyright (c) 2018-2020 AT&T Intellectual Property.
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

# This container uses a 2 stage build!
# Tips and tricks were learned from: https://pythonspeed.com/articles/multi-stage-docker-python/
FROM python:3.8-alpine AS compile-image
# Gevent needs gcc
RUN apk update && apk add gcc musl-dev

# Switch to a non-root user for security reasons
# This is only really needed in stage 2 however this makes the copying easier and straitforward! --user doesn't do the same thing if run as root!
RUN addgroup -S a1user && adduser -S -G a1user a1user
USER a1user

# Speed hack; we install gevent FIRST because when building repeatedly (eg during dev) and only changing a1 code, we do not need to keep compiling gevent which takes forever
RUN pip install --upgrade pip && pip install --user gevent
COPY setup.py /home/a1user/
COPY a1/ /home/a1user/a1
RUN pip install --user /home/a1user

###########
# 2nd stage
FROM python:3.8-alpine
# dir that rmr routing file temp goes into
RUN mkdir -p /opt/route/
# python copy; this basically makes the 2 stage python build work
COPY --from=compile-image /home/a1user/.local /home/a1user/.local
# copy rmr .so from the builder image
COPY --from=nexus3.o-ran-sc.org:10004/bldr-alpine3-go:5-a3.11-nng-rmr3 /usr/local/lib64/librmr_si.so /usr/local/lib64/librmr_si.so
# Switch to a non-root user for security reasons. a1 does not currently write into any dirs so no chowns are needed at this time.
RUN addgroup -S a1user && adduser -S -G a1user a1user
USER a1user
# misc setups
EXPOSE 10000
ENV LD_LIBRARY_PATH /usr/local/lib/:/usr/local/lib64
ENV RMR_SEED_RT /opt/route/local.rt
ENV PYTHONUNBUFFERED 1
# This step is critical
ENV PATH=/home/a1user/.local/bin:$PATH

# Run!
CMD run.py
