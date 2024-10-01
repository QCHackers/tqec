#!/usr/bin/env bash

tqec dae2circuits examples/assets/logical_cnot.dae \
  --out-dir out \
  -k 1 2 3 \
  --obs-include 0 \
  --add-detectors
