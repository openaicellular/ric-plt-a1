#!/bin/sh
kubectl get pods --namespace=default | awk '{ print $1 }' | egrep '^a1-a1mediator-' | xargs kubectl logs  > log.txt 2>&1
kubectl get pods --namespace=default | awk '{ print $1 }' | egrep '^testreceiver-' | xargs -I X kubectl logs X testreceiver  >> log.txt 2>&1
kubectl get pods --namespace=default | awk '{ print $1 }' | egrep '^testreceiver-' | xargs -I X kubectl logs X delayreceiver  >> log.txt 2>&1
