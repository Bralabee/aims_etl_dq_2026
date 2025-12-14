# CI/CD Setup Guide - AIMS Data Platform

**Version:** 1.0  
**Date:** 10 December 2025  
**Estimated Setup Time:** 2-3 hours

---

## Overview

This guide walks you through setting up the complete CI/CD infrastructure for the AIMS Data Platform, including:

- ✅ **Azure DevOps Pipeline** (4-stage pipeline with approvals)
- ✅ **GitHub Actions Workflow** (7-job workflow with matrix testing)
- ✅ **Environment Configuration** (Dev + Prod)
- ✅ **Secret Management** (Azure credentials, tokens)
- ✅ **Branch Protection** (PR checks, approvals)

**Prerequisites:**
- Azure DevOps organization access
- GitHub repository access
- Azure subscription (for deployments)
- Admin permissions for both platforms

---

## Table of Contents

1. [Quick Start Checklist](#quick-start-checklist)
2. [Azure DevOps Setup](#azure-devops-setup)
3. [GitHub Actions Setup](#github-actions-setup)
4. [Testing Your Pipelines](#testing-your-pipelines)
5. [Troubleshooting](#troubleshooting)
6. [Best Practices](#best-practices)

---

## Quick Start Checklist

### Pre-Setup (5 minutes)

- [ ] Verify repository structure is correct
- [ ] Confirm both pipeline files exist:
  - [ ] `azure-pipelines.yml` at repository root
  - [ ] `.github/workflows/ci-cd.yml` in .github/workflows/
- [ ] Gather credentials:
  - [ ] Azure subscription ID
  - [ ] Azure tenant ID
  - [ ] Azure service principal credentials
  - [ ] Codecov token (optional but recommended)

### Azure DevOps Setup (45-60 minutes)

- [ ] Create Azure DevOps project
- [ ] Connect repository
- [ ] Create service connection to Azure
- [ ] Create environments (Dev, Prod)
- [ ] Configure pipeline
- [ ] Run first build

### GitHub Actions Setup (45-60 minutes)

- [ ] Add repository secrets
- [ ] Configure environments with protection rules
- [ ] Set up branch protection
- [ ] Enable Codecov integration
- [ ] Run first workflow
- [ ] Test PR checks

---

## Azure DevOps Setup

### Step 1: Create Azure DevOps Project (10 minutes)

1. **Navigate to Azure DevOps**
   - Go to https://dev.azure.com/{your-org}
   - Or create new org: https://aex.dev.azure.com/

2. **Create New Project**
   ```
   Project Name: AIMS-Data-Platform
   Visibility: Private
   Version Control: Git
   Work Item Process: Agile
   ```

3. **Verify Project Creation**
   - Project should appear in your organization
   - Note the project URL for later

### Step 2: Connect Repository (15 minutes)

#### Option A: Import from GitHub (Recommended)

1. **Navigate to Repos**
   - Click "Repos" in left sidebar
   - Click "Import" button

2. **Configure Import**
   ```
   Clone URL: https://github.com/Bralabee/aims_etl_dq_2026.git
   Requires Authentication: Yes (if private)
   Repository Name: aims_etl_dq_2026
   ```

3. **Authenticate with GitHub**
   - Use GitHub personal access token
   - Token needs `repo` scope

4. **Verify Import**
   - Check that all branches imported
   - Verify `azure-pipelines.yml` exists at root

#### Option B: Mirror Repository (Alternative)

If you want to keep GitHub as source of truth:

1. **Keep GitHub as Primary**
   - Azure DevOps can trigger from GitHub directly
   - No need to import/sync

2. **Configure GitHub Connection**
   - Go to Project Settings → Service Connections
   - Click "New service connection" → GitHub
   - Authorize Azure DevOps app on GitHub

### Step 3: Create Service Connection to Azure (15 minutes)

1. **Navigate to Service Connections**
   ```
   Project Settings → Pipelines → Service connections
   ```

2. **Create Azure Resource Manager Connection**
   - Click "New service connection"
   - Select "Azure Resource Manager"
   - Click "Next"

3. **Choose Authentication Method**
   
   **Option A: Service Principal (Automatic) - Recommended**
   ```
   Authentication Method: Service Principal (automatic)
   Scope Level: Subscription
   Subscription: <Your Azure Subscription>
   Resource Group: <Leave empty or select specific RG>
   Service Connection Name: AIMS-Azure-Connection
   Grant access permission to all pipelines: ✓ (check)
   ```

   **Option B: Service Principal (Manual)**
   
   If automatic doesn't work, create manually:
   
   ```bash
   # In Azure CLI
   az ad sp create-for-rbac --name "aims-devops-sp" \
     --role contributor \
     --scopes /subscriptions/{subscription-id} \
     --sdk-auth
   ```
   
   Copy the JSON output and fill in:
   ```
   Subscription ID: <from JSON>
   Subscription Name: <from Azure>
   Service Principal ID: <clientId from JSON>
   Service Principal Key: <clientSecret from JSON>
   Tenant ID: <tenantId from JSON>
   ```

4. **Verify Connection**
   - Click "Verify" button
   - Should show green checkmark
   - Save the connection

### Step 4: Create Environments (10 minutes)

1. **Navigate to Environments**
   ```
   Pipelines → Environments
   ```

2. **Create Development Environment**
   ```
   Name: AIMS-Dev
   Description: Development environment for AIMS platform
   Resource: None (we'll configure later)
   ```

3. **Create Production Environment**
   ```
   Name: AIMS-Production
   Description: Production environment for AIMS platform
   Resource: None (we'll configure later)
   ```

4. **Configure Production Approvals**
   - Click on "AIMS-Production" environment
   - Click "..." menu → "Approvals and checks"
   - Click "+" → "Approvals"
   - Configure:
     ```
     Approvers: <Add yourself and team leads>
     Minimum approvers: 1
     Timeout: 60 days
     Instructions: "Review deployment and approve for production"
     ```

### Step 5: Configure Pipeline (10 minutes)

1. **Navigate to Pipelines**
   ```
   Pipelines → Pipelines → New Pipeline
   ```

2. **Select Repository**
   - Choose "Azure Repos Git" (if imported)
   - Or "GitHub" (if using GitHub directly)
   - Select `aims_etl_dq_2026` repository

3. **Configure Pipeline**
   - Select "Existing Azure Pipelines YAML file"
   - Branch: `master`
   - Path: `/azure-pipelines.yml`
   - Click "Continue"

4. **Review and Run**
   - Review the YAML (should show 4 stages)
   - Click "Run" to trigger first build
   - Or click "Save" if you want to configure more first

5. **Configure Variables (Optional)**
   
   If you need custom variables:
   ```
   Pipelines → Library → + Variable group
   
   Variable Group Name: AIMS-Config
   Variables:
     - PYTHON_VERSION: 3.11
     - AIMS_ENV: development
     - THRESHOLD: 85.0
   
   Link to pipeline: AIMS-Data-Platform
   ```

### Step 6: Run First Build (5 minutes)

1. **Trigger Pipeline**
   - Go to Pipelines → Pipelines
   - Select your pipeline
   - Click "Run pipeline"
   - Select branch: `master` or `develop`
   - Click "Run"

2. **Monitor Execution**
   - Watch stages execute:
     1. ✓ Build (BuildDQLibrary + BuildAIMSPlatform)
     2. ✓ DataQualityValidation
     3. ⏸️ DeployDev (only on develop branch)
     4. ⏸️ DeployProd (only on master, needs approval)

3. **Verify Success**
   - All stages should be green
   - Check test results published
   - Verify artifacts uploaded
   - Check DQ validation results

### Expected Output

```
Stage: Build
  Job: BuildDQLibrary
    - Setup Python: ✓
    - Install dependencies: ✓
    - Run tests: ✓ 15/15 passed
    - Code coverage: ✓ XX%
    - Build wheel: ✓
    - Publish artifacts: ✓

  Job: BuildAIMSPlatform
    - Setup Python: ✓
    - Install dependencies: ✓
    - Run tests: ✓
    - Publish results: ✓

Stage: DataQualityValidation
  Job: RunDQValidation
    - Setup Python: ✓
    - Run validation: ✓ 68 files validated
    - Extract metrics: ✓ 50 passed, 18 failed
    - Publish results: ✓
    - Warning: 18 files below threshold

Stage: DeployDev (if develop branch)
  - Deploy to Dev: ✓

Stage: DeployProd (if master branch)
  - Waiting for approval...
```

---

## GitHub Actions Setup

### Step 1: Add Repository Secrets (15 minutes)

1. **Navigate to Repository Settings**
   ```
   GitHub Repository → Settings → Secrets and variables → Actions
   ```

2. **Create Azure Credentials Secret**
   
   First, create a service principal (if not done yet):
   
   ```bash
   # In Azure CLI
   az ad sp create-for-rbac --name "aims-github-actions" \
     --role contributor \
     --scopes /subscriptions/{subscription-id} \
     --sdk-auth
   ```
   
   Copy the JSON output:
   ```json
   {
     "clientId": "xxx",
     "clientSecret": "xxx",
     "subscriptionId": "xxx",
     "tenantId": "xxx",
     "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
     "resourceManagerEndpointUrl": "https://management.azure.com/",
     "activeDirectoryGraphResourceId": "https://graph.windows.net/",
     "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
     "galleryEndpointUrl": "https://gallery.azure.com/",
     "managementEndpointUrl": "https://management.core.windows.net/"
   }
   ```

3. **Add Secrets**
   
   Click "New repository secret" for each:
   
   **Required:**
   ```
   Name: AZURE_CREDENTIALS
   Value: <paste entire JSON from above>
   
   Name: AZURE_SUBSCRIPTION_ID
   Value: <your subscription ID>
   
   Name: AZURE_TENANT_ID
   Value: <your tenant ID>
   ```
   
   **Optional (but recommended):**
   ```
   Name: CODECOV_TOKEN
   Value: <get from https://codecov.io after signup>
   
   Name: SLACK_WEBHOOK_URL
   Value: <Slack webhook for notifications>
   ```

### Step 2: Configure Environments (15 minutes)

1. **Navigate to Environments**
   ```
   Settings → Environments → New environment
   ```

2. **Create Development Environment**
   ```
   Name: development
   
   Environment protection rules:
   - ☐ Required reviewers (not needed for dev)
   - ☑ Wait timer: 0 minutes
   - ☑ Deployment branches: Only develop branch
   ```

3. **Create Production Environment**
   ```
   Name: production
   
   Environment protection rules:
   - ☑ Required reviewers: <Add yourself and team leads>
   - ☑ Wait timer: 5 minutes
   - ☑ Deployment branches: Only master branch
   - ☑ Prevent self-review: Yes
   ```

4. **Add Environment Secrets (Optional)**
   
   For each environment, you can add specific secrets:
   ```
   Environment: development
     - DEV_DATABASE_URL
     - DEV_API_KEY
   
   Environment: production
     - PROD_DATABASE_URL
     - PROD_API_KEY
   ```

### Step 3: Set Up Branch Protection (15 minutes)

1. **Navigate to Branch Settings**
   ```
   Settings → Branches → Add rule
   ```

2. **Protect Master Branch**
   ```
   Branch name pattern: master
   
   Protect matching branches:
   ☑ Require a pull request before merging
     ☑ Require approvals: 1
     ☑ Dismiss stale pull request approvals when new commits are pushed
     ☐ Require review from Code Owners
   
   ☑ Require status checks to pass before merging
     ☑ Require branches to be up to date before merging
     Status checks that are required:
       - build-dq-library
       - build-aims-platform
       - dq-validation
   
   ☑ Require conversation resolution before merging
   ☑ Require signed commits (optional, but recommended)
   ☐ Require linear history
   ☑ Include administrators (uncheck if you need bypass)
   
   ☑ Restrict who can push to matching branches
     - Add: <admin team only>
   ```

3. **Protect Develop Branch**
   ```
   Branch name pattern: develop
   
   Protect matching branches:
   ☑ Require a pull request before merging
     ☑ Require approvals: 1
   
   ☑ Require status checks to pass before merging
     Status checks that are required:
       - build-dq-library
       - build-aims-platform
       - dq-validation
   
   ☐ Include administrators (allow admins to bypass)
   ```

### Step 4: Enable Codecov Integration (10 minutes)

1. **Sign Up for Codecov**
   - Go to https://codecov.io
   - Sign in with GitHub
   - Authorize Codecov app

2. **Add Repository**
   - Click "Add repository"
   - Select `Bralabee/aims_etl_dq_2026`
   - Copy the Codecov token

3. **Add Token to GitHub Secrets**
   - Already done in Step 1
   - If not: Settings → Secrets → New secret
   - Name: `CODECOV_TOKEN`
   - Value: <paste token>

4. **Configure Codecov (Optional)**
   
   Create `.codecov.yml` at repository root:
   ```yaml
   coverage:
     status:
       project:
         default:
           target: 80%
           threshold: 5%
       patch:
         default:
           target: 80%
   
   comment:
     require_changes: true
     layout: "reach, diff, flags, files"
     behavior: default
   ```

### Step 5: Run First Workflow (5 minutes)

1. **Trigger Workflow Manually**
   ```
   Actions → CI/CD → Run workflow
   Branch: master
   Click "Run workflow"
   ```

2. **Or Trigger via Push**
   ```bash
   git checkout develop
   git commit --allow-empty -m "Test CI/CD workflow"
   git push origin develop
   ```

3. **Monitor Execution**
   - Go to Actions tab
   - Click on the running workflow
   - Watch jobs execute in matrix:
     1. ✓ build-dq-library (6 jobs: 3 Python × 2 OS)
     2. ✓ build-aims-platform (6 jobs)
     3. ✓ dq-validation
     4. ✓ publish-test-results
     5. ⏸️ create-release (only on tags)
     6. ⏸️ deploy-dev (only on develop)
     7. ⏸️ deploy-prod (only on master)

4. **Verify Success**
   - All jobs should be green
   - Check for PR comment (if PR triggered)
   - Verify Codecov report
   - Check artifacts uploaded

### Expected Output

```
Job: build-dq-library (ubuntu-latest, 3.11)
  ✓ Set up Python 3.11
  ✓ Cache dependencies
  ✓ Install dependencies
  ✓ Run tests with pytest
  ✓ Upload coverage to Codecov
  ✓ Build wheel
  ✓ Upload wheel artifact

Job: build-aims-platform (windows-latest, 3.10)
  ✓ Set up Python 3.10
  ✓ Download DQ library wheel
  ✓ Install DQ library
  ✓ Install AIMS dependencies
  ✓ Run AIMS tests
  ✓ Upload coverage

Job: dq-validation
  ✓ Set up Python
  ✓ Download DQ library wheel
  ✓ Install dependencies
  ✓ Run validation pipeline
  ✓ Extract validation metrics
    - Total: 68
    - Passed: 50
    - Failed: 18
    - Threshold: 85%
  ✓ Upload validation results
  ✓ Comment on PR (if applicable)

All jobs completed in 8m 23s
```

### Step 6: Test PR Checks (10 minutes)

1. **Create Test Branch**
   ```bash
   git checkout develop
   git checkout -b test/ci-cd-checks
   echo "# Test CI/CD" >> README.md
   git add README.md
   git commit -m "Test: CI/CD checks on PR"
   git push origin test/ci-cd-checks
   ```

2. **Create Pull Request**
   - Go to GitHub → Pull requests → New PR
   - Base: `develop`, Compare: `test/ci-cd-checks`
   - Create PR

3. **Verify Checks Run**
   - Watch checks execute at bottom of PR
   - Should see all required checks:
     - ✓ build-dq-library
     - ✓ build-aims-platform
     - ✓ dq-validation
   - Wait for PR comment with DQ metrics

4. **Verify Comment Posted**
   
   Should see bot comment:
   ```
   ## Data Quality Validation Results
   
   | Metric | Value |
   |--------|-------|
   | Total Files | 68 |
   | Passed | 50 |
   | Failed | 18 |
   | Success Rate | 73.5% |
   | Threshold | 85% |
   
   ⚠️ Warning: 18 files below threshold
   ```

5. **Merge PR (Optional)**
   - If all checks pass, merge the PR
   - Watch deploy-dev job execute
   - Verify deployment successful

---

## Testing Your Pipelines

### Test 1: Build and Test (Both Platforms)

**Azure DevOps:**
```bash
# Trigger via commit
git checkout develop
git commit --allow-empty -m "Test: Azure DevOps build"
git push origin develop

# Watch in Azure DevOps
# https://dev.azure.com/{org}/{project}/_build
```

**GitHub Actions:**
```bash
# Trigger via commit
git checkout develop
git commit --allow-empty -m "Test: GitHub Actions build"
git push origin develop

# Watch in GitHub
# https://github.com/Bralabee/aims_etl_dq_2026/actions
```

**Expected:** Both should run Build and DataQualityValidation stages

### Test 2: Pull Request Checks (GitHub only)

```bash
# Create feature branch
git checkout -b feature/test-pr-checks
echo "test" > test.txt
git add test.txt
git commit -m "Test PR checks"
git push origin feature/test-pr-checks

# Create PR on GitHub
# Base: develop, Compare: feature/test-pr-checks
```

**Expected:** All checks run, PR comment posted with DQ metrics

### Test 3: Development Deployment

```bash
# Merge to develop
git checkout develop
git merge feature/test-pr-checks
git push origin develop
```

**Expected:**
- Azure DevOps: DeployDev stage executes
- GitHub Actions: deploy-dev job executes

### Test 4: Production Deployment (Requires Approval)

```bash
# Merge to master
git checkout master
git merge develop
git push origin master
```

**Expected:**
- Azure DevOps: DeployProd stage waits for approval
- GitHub Actions: deploy-prod job waits for approval
- Approve deployment manually
- Verify deployment executes

### Test 5: Release Creation (GitHub only)

```bash
# Create version tag
git checkout master
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

**Expected:**
- create-release job executes
- GitHub release created with artifacts
- Wheel uploaded to release

---

## Troubleshooting

### Common Issues

#### Azure DevOps

**Issue: "Service connection not authorized"**

Solution:
```
1. Go to Project Settings → Service connections
2. Click on "AIMS-Azure-Connection"
3. Click "Security"
4. Check "Grant access permission to all pipelines"
5. Save
```

**Issue: "Environment not found"**

Solution:
```
1. Go to Pipelines → Environments
2. Verify "AIMS-Dev" and "AIMS-Production" exist
3. Exact spelling matters (case-sensitive)
4. Re-save pipeline if needed
```

**Issue: "Tests not publishing"**

Solution:
```yaml
# Verify this task in azure-pipelines.yml
- task: PublishTestResults@2
  condition: always()
  inputs:
    testResultsFormat: 'JUnit'
    testResultsFiles: '**/test-results.xml'
```

**Issue: "Artifacts not uploading"**

Solution:
```yaml
# Verify this task
- task: PublishPipelineArtifact@1
  inputs:
    targetPath: '$(System.DefaultWorkingDirectory)/2_DATA_QUALITY_LIBRARY/dist'
    artifactName: 'dq-library-wheel'
```

#### GitHub Actions

**Issue: "Secret not found"**

Solution:
```
1. Settings → Secrets and variables → Actions
2. Verify secret name matches exactly (case-sensitive)
3. In workflow: ${{ secrets.AZURE_CREDENTIALS }}
4. Re-add secret if needed
```

**Issue: "Environment not found"**

Solution:
```
1. Settings → Environments
2. Verify "development" and "production" exist
3. Lowercase matters!
4. Check environment name in workflow YAML
```

**Issue: "Codecov upload failing"**

Solution:
```yaml
# Add fail_ci_if_error: false to continue on error
- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    fail_ci_if_error: false
```

**Issue: "Matrix job failing on Windows"**

Solution:
```yaml
# Use cross-platform path separator
- name: Install DQ library
  run: |
    python -m pip install dist/*.whl
  # Instead of:
  # run: python -m pip install dist/$(ls dist/)
```

**Issue: "PR comment not posting"**

Solution:
```
1. Verify workflow has permissions:
   permissions:
     contents: read
     pull-requests: write
     
2. Check if PR is from fork (limited permissions)
3. Verify actions/github-script action is correct version
```

### Debug Mode

**Azure DevOps:**
```
1. Edit pipeline
2. Click Variables
3. Add variable: system.debug = true
4. Run pipeline
```

**GitHub Actions:**
```
1. Go to Actions → workflow
2. Re-run jobs → Enable debug logging
3. Or add to workflow:
   env:
     ACTIONS_STEP_DEBUG: true
```

---

## Best Practices

### General

1. **Start with Develop Branch**
   - Test all changes on develop first
   - Only merge to master after validation
   - Use feature branches for development

2. **Monitor First Runs**
   - Watch first pipeline execution closely
   - Fix issues immediately
   - Don't merge broken pipelines

3. **Use Consistent Naming**
   - Service connections: `AIMS-Azure-Connection`
   - Environments: `AIMS-Dev`, `AIMS-Production` (Azure)
   - Environments: `development`, `production` (GitHub)

4. **Secure Secrets**
   - Never commit secrets to repository
   - Rotate credentials regularly
   - Use least-privilege service principals

### Azure DevOps Specific

1. **Use Service Connections**
   - Don't hardcode credentials
   - Create separate connections for each environment
   - Example: `AIMS-Azure-Dev`, `AIMS-Azure-Prod`

2. **Configure Notifications**
   ```
   Project Settings → Notifications
   Add rules for:
   - Build failures
   - Deployment requests
   - Approval requests
   ```

3. **Use Variable Groups**
   ```
   Pipelines → Library → + Variable group
   Group by environment:
   - AIMS-Dev-Config
   - AIMS-Prod-Config
   ```

### GitHub Actions Specific

1. **Use Environments**
   - Always use environments for deployments
   - Configure protection rules
   - Add required reviewers

2. **Cache Dependencies**
   ```yaml
   - uses: actions/cache@v3
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
   ```

3. **Use Matrix Wisely**
   - Don't overdo it (costs runner minutes)
   - Current setup: 3 Python × 2 OS = 6 jobs
   - Consider: 2 Python × 2 OS = 4 jobs for speed

4. **Monitor Usage**
   ```
   Settings → Billing → Actions minutes
   Check usage regularly
   Free tier: 2000 minutes/month
   ```

---

## Next Steps

After completing this setup:

1. ✅ **Verify Both Pipelines Work**
   - [ ] Azure DevOps pipeline runs successfully
   - [ ] GitHub Actions workflow runs successfully
   - [ ] All tests pass
   - [ ] DQ validation completes

2. ✅ **Configure Notifications**
   - [ ] Slack/Teams webhooks
   - [ ] Email notifications
   - [ ] PR comments working

3. ✅ **Document Team Workflows**
   - [ ] How to create PRs
   - [ ] How to trigger deployments
   - [ ] How to review DQ results
   - [ ] How to approve production deployments

4. ✅ **Train Team Members**
   - [ ] Show how to read pipeline results
   - [ ] Explain approval process
   - [ ] Demo PR workflow
   - [ ] Share this guide

5. ✅ **Monitor and Optimize**
   - [ ] Track build times
   - [ ] Optimize slow jobs
   - [ ] Review runner costs
   - [ ] Adjust matrix if needed

---

## Quick Reference

### Azure DevOps URLs

```
Organization: https://dev.azure.com/{your-org}
Project: https://dev.azure.com/{your-org}/AIMS-Data-Platform
Pipelines: https://dev.azure.com/{your-org}/AIMS-Data-Platform/_build
Environments: https://dev.azure.com/{your-org}/AIMS-Data-Platform/_environments
Service Connections: https://dev.azure.com/{your-org}/AIMS-Data-Platform/_settings/adminservices
```

### GitHub URLs

```
Repository: https://github.com/Bralabee/aims_etl_dq_2026
Actions: https://github.com/Bralabee/aims_etl_dq_2026/actions
Settings: https://github.com/Bralabee/aims_etl_dq_2026/settings
Secrets: https://github.com/Bralabee/aims_etl_dq_2026/settings/secrets/actions
Environments: https://github.com/Bralabee/aims_etl_dq_2026/settings/environments
Branches: https://github.com/Bralabee/aims_etl_dq_2026/settings/branches
```

### CLI Commands

**Azure DevOps:**
```bash
# Install Azure DevOps extension
az extension add --name azure-devops

# Set default org and project
az devops configure --defaults organization=https://dev.azure.com/{your-org} project=AIMS-Data-Platform

# List pipelines
az pipelines list

# Run pipeline
az pipelines run --name "AIMS-Data-Platform"

# Show pipeline runs
az pipelines runs list
```

**GitHub CLI:**
```bash
# Install GitHub CLI
# https://cli.github.com/

# List workflows
gh workflow list

# Run workflow
gh workflow run ci-cd.yml

# View workflow run
gh run list

# View logs
gh run view {run-id} --log
```

---

## Support

For issues or questions:

1. **Check logs first** (both platforms have detailed logs)
2. **Review this guide** (most issues covered in Troubleshooting)
3. **Check Azure DevOps docs**: https://docs.microsoft.com/en-us/azure/devops/
4. **Check GitHub Actions docs**: https://docs.github.com/en/actions
5. **Contact team lead** or DevOps engineer

---

**Guide Version:** 1.0  
**Last Updated:** 10 December 2025  
**Maintainer:** AIMS Data Platform Team
