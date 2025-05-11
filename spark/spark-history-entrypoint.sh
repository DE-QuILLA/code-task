#!/bin/bash

echo "Starting Spark History Server..."
/opt/spark/bin/spark-class org.apache.spark.deploy.history.HistoryServer
