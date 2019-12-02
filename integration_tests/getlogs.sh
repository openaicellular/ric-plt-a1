#!/bin/sh
echo "\n\n a1" >> log.txt
kubectl get pods --namespace=default | awk '{ print $1 }' | egrep '^a1-a1mediator-' | xargs kubectl logs  > log.txt 2>&1

echo "\n\n test receiver" >> log.txt
kubectl get pods --namespace=default | awk '{ print $1 }' | egrep '^testreceiver-' | xargs -I X kubectl logs X testreceiver  >> log.txt 2>&1

echo "\n\n delay" >> log.txt
kubectl get pods --namespace=default | awk '{ print $1 }' | egrep '^testreceiver-' | xargs -I X kubectl logs X delayreceiver  >> log.txt 2>&1

echo "\n\n query" >> log.txt
kubectl get pods --namespace=default | awk '{ print $1 }' | egrep '^testreceiver-' | xargs -I X kubectl logs X queryreceiver  >> log.txt 2>&1
