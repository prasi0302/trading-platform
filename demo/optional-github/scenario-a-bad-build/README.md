# Lab 1 — Build Failure: Docker image not found

A developer changes the Dockerfile base image to a tag that does not exist. The Docker build fails in GitHub Actions; the application is never deployed and the pipeline is broken.

## Flow

```
Bad Dockerfile (python:3.12-nonexistent)
  -> Docker build fails ("manifest unknown")
  -> notify-devops-agent job sends a webhook on pipeline failure
  -> AWS DevOps Agent auto-investigates
```

## What the agent does

- Reads the GitHub pipeline status
- Identifies the failed build job
- Reads the job logs (sees `manifest unknown`)
- Reads the commit diff
- Identifies the Dockerfile change that caused the failure
- Produces a mitigation specification with the fix

## Data sources correlated

- GitHub: pipeline status, job logs, commit diff

## Expected output

Inline analysis: identifies the bad base image, shows the commit author, and recommends valid image tags.

## Scripts

- `inject.sh` — injects the failure (changes the base image to a non-existent tag, commits, and pushes)
- `fix.sh` — reverts to the working base image, commits, and pushes

## Usage

```bash
# Inject the failure
./demo/lab1-build-failure/inject.sh

# After investigation, fix it
./demo/lab1-build-failure/fix.sh
```
