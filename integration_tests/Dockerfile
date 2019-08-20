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
FROM python:3.7-alpine

COPY receiver.py /

# copy NNG and rmr out of the  CI builder nng
COPY --from=nexus3.o-ran-sc.org:10004/bldr-alpine3:3-a3.9 /usr/local/lib64/libnng.so /usr/local/lib64/libnng.so
COPY --from=nexus3.o-ran-sc.org:10004/bldr-alpine3:3-a3.9 /usr/local/lib64/librmr_nng.so /usr/local/lib64/librmr_nng.so

# Install RMr python bindings
RUN pip install --upgrade pip
RUN pip install rmr==0.10.8

# rmr setups
RUN mkdir -p /opt/route/
ENV LD_LIBRARY_PATH /usr/local/lib:/usr/local/lib64
ENV RMR_SEED_RT /opt/route/local.rt

WORKDIR /
CMD ["python","-u","receiver.py"]
