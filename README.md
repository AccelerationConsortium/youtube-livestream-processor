# Video Processing

This project implements a distributed system for the automated processing of hardware livestreams by accelerating/removing stale video sections. The system is segmented into three sections which can be run on independent machines, downloading, processing, and uploading.

These segments are synced by a common `progress.json` file with filelocks for mutual exclusion.

## Downloading

## Processing

## Uploading
