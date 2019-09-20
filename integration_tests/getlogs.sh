#!/bin/sh
kubectl get pods --namespace=default | awk '{ print $1 }' | egrep '^a1-a1mediator-' | xargs kubectl logs
kubectl get pods --namespace=default | awk '{ print $1 }' | egrep '^testreceiver-' | xargs -I X kubectl logs X testreceiver
kubectl get pods --namespace=default | awk '{ print $1 }' | egrep '^testreceiver-' | xargs -I X kubectl logs X delayreceiver

