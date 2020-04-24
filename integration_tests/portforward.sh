#!/bin/bash
# fail on error
set -eux
kubectl port-forward $(kubectl get pods --namespace default -l "app.kubernetes.io/name=a1mediator,app.kubernetes.io/instance=a1" -o jsonpath="{.items[0].metadata.name}") 10000:10000 2>&1 > forward.log &
