# Lab 1: Build Failure — Docker Image Not Found

## Scenario
A developer changes the Dockerfile base image to one that doesn't exist. The Docker build fails in GitHub Actions — the application is never deployed, but the pipeline is broken.

## Flow
```
Bad Dockerfile (python:3.12-nonexistent)
  → Build fails "manifest not found"
  → GitHub webhook (status = failed)
  → DevOps Agent auto-investigates
```

## What the agent does
- Reads GitHub pipeline status
- Identifies the failed build job
- Reads job logs (sees "manifest unknown")
- Reads the commit diff
- Identifies the Dockerfile change that caused it
- Produces mitigation spec with fix

## Data sources correlated
- GitHub (pipeline status, job logs, commit diff)

## Expected output
Inline analysis — identifies bad base image, shows commit author, recommends valid image tags.

## Scripts
- `inject.sh` — Injects the failure (changes base image to non-existent tag)
- `fix.sh` — Reverts to the working state

## Usage
```bash
# Inject the failure
./demo/lab1-dockerfile-bad-image/inject.sh

# After investigation, fix it
./demo/lab1-dockerfile-bad-image/fix.sh
```
