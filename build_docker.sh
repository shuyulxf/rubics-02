#!/bin/bash
NAMESPACE="${1:-codebase_b909_app}"
docker build -t "$NAMESPACE" .
