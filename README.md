# sast-ai-dvc

Data Version Control (DVC) repository for SAST AI workflow data.

## Overview

This repository uses:
- **Git** for code and metadata versioning
- **Git tags** for version releases
- **DVC** for large file storage and versioning

## Prerequisites

```bash
# Install DVC with S3 support
pip install dvc dvc-s3
```

## 1. Versioning with Git Tags

We use Git tags to mark specific versions of the repository and its data.

### View available versions
```bash
git tag
```

### Create a new version
```bash
# After making changes and committing
git tag v1.1.0
git push origin v1.1.0
```

### Checkout a specific version
```bash
git checkout v1.0.0
```

## 2. Pushing a New Version with DVC

When you have new or updated data:

```bash
# 1. Add/update your data files
# (DVC is already tracking them)

# 2. Push data to DVC remote storage
dvc push

# 3. Commit the updated .dvc files
git add *.dvc
git commit -m "Update data for version X.X.X"

# 4. Create and push a new version tag
git tag vX.X.X
git push origin main
git push origin vX.X.X
```

## 3. Clone Everything with DVC

To get the complete repository with all data:

```bash
# 1. Clone the Git repository
git clone <repository-url>
cd dvc-repo

# 2. Pull all DVC-tracked data
dvc pull
```

### Clone a specific version
```bash
# Clone and checkout a specific tag
git clone <repository-url>
cd dvc-repo
git checkout v1.0.0
dvc pull
```

## 4. Get a Single File with DVC

To download just one specific file without cloning the entire repository:

```bash
# Download a single file to current directory
dvc get . path/to/file

# Download to a specific location
dvc get . path/to/file -o ./where-to-put-file

# Download from a specific version/tag
dvc get . path/to/file --rev v1.0.0 -o ./output-file
```

### Examples

```bash
# Get a specific ground truth sheet
dvc get . ground_truth_sheets/acl-2.3.2-1.el10.xlsx -o ./acl.xlsx

# Get known non-issues for a specific package
dvc get . known-non-issues-el10/acl/ignore.err -o ./acl-ignore.err

# Get from a specific version
dvc get . config.yaml --rev v1.0.0 -o ./config-v1.0.yaml
```

## Repository Structure

```
.
├── config.yaml                  # Configuration file
├── ground_truth_sheets/         # DVC-tracked: Ground truth data
├── known-non-issues-el10/       # DVC-tracked: Known non-issues
├── prompts/                     # DVC-tracked: AI prompts
├── testing-data-nvrs.yaml       # DVC-tracked: Test data
└── *.dvc                        # DVC metadata files
```

## DVC Remote Storage

DVC data is stored in MinIO S3-compatible storage. Configuration is in `.dvc/config`.

## Troubleshooting

### Connection issues
Ensure you have access to the DVC remote storage endpoint. You may need VPN access.

### Missing dvc-s3
If you get "No module named 'dvc_s3'":
```bash
pip install dvc-s3
```