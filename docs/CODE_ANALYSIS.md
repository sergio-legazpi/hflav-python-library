# Code Analysis Guide

## Overview

This project uses SonarQube for static code analysis to ensure code quality, identify bugs, detect security vulnerabilities, and maintain code standards.

## Prerequisites

- Docker and Docker Compose
- SonarQube extension for VS Code (optional but recommended)
- Python coverage tools (already included in dev dependencies)

## Setting Up SonarQube Locally

### 1. Start SonarQube Server

Launch the SonarQube server using Docker Compose:

```bash
docker compose up
```

This will start the SonarQube server on `http://localhost:9000`.

### 2. Initial Configuration

If this is your first time running SonarQube:

1. **Access SonarQube**: Open your browser and navigate to `http://localhost:9000`

2. **Login**: Use the default credentials:
   - Username: `admin`
   - Password: `admin`
   - You'll be prompted to change the password on first login

3. **Create a Local Project**:
   - Click on "Create Project" → "Manually"
   - Project key: `hflav-project` (or your preferred key)
   - Project name: `HFLAV FAIR Client`
   - Click "Set Up"

4. **Generate Token**:
   - Choose "Locally"
   - Generate a token (save it for later use)
   - Select "Python" as your project type
   - Copy the provided command for later

### 3. Configure VS Code Extension (Optional)

If you're using the SonarQube VS Code extension:

1. **Install the extension**: Search for "SonarQube" in VS Code extensions marketplace

2. **Configure connection**:
   - Open VS Code settings
   - Search for "SonarQube"
   - Add connection:
     - Server URL: `http://localhost:9000`
     - Connection name: `sonar-hflav-connection`
     - Token: Use the token generated in step 4

## Running Code Analysis

### 1. Generate Coverage Data

Before running SonarQube analysis, you need to generate code coverage data:

```bash
coverage run -m pytest
coverage xml
```

This will:
- Run all tests with coverage tracking
- Generate a `coverage.xml` file that SonarQube will use

### 2. Run SonarQube Scanner

Execute the SonarQube scanner with your project configuration:

```bash
pysonar \
  --sonar-host-url=http://localhost:9000 \
  --sonar-token=<YOUR_TOKEN> \
  --sonar-project-key=<YOUR_PROJECT_KEY>
```

Replace `<YOUR_TOKEN>` and `<YOUR_PROJECT_KEY>` with the values from your SonarQube setup.

Alternatively, if you have a `sonar-project.properties` file configured, you can simply run:

```bash
sonar-scanner
```

### 3. View Results

After the analysis completes:

1. Go to `http://localhost:9000`
2. Navigate to your project
3. Review the analysis results:
   - **Bugs**: Potential bugs in the code
   - **Vulnerabilities**: Security issues
   - **Code Smells**: Maintainability issues
   - **Coverage**: Test coverage metrics
   - **Duplications**: Duplicated code blocks

## Understanding SonarQube Metrics

### Quality Gate

The Quality Gate is a set of conditions that must be met for your code to pass analysis. Default conditions include:

- Coverage on new code > 80%
- Duplicated lines on new code < 3%
- Maintainability rating on new code = A
- Reliability rating on new code = A
- Security rating on new code = A

### Issue Severity Levels

- **Blocker**: Must be fixed immediately (e.g., critical security vulnerability)
- **Critical**: Should be fixed ASAP (e.g., bug that could cause data loss)
- **Major**: Should be fixed (e.g., significant code smell)
- **Minor**: Could be fixed (e.g., minor code smell)
- **Info**: Informational (e.g., suggestion for improvement)

## Analysis Configuration

### sonar-project.properties

The project includes a `sonar-project.properties` file with configuration settings:

```properties
sonar.projectKey=your-project-key
sonar.projectName=HFLAV FAIR Client
sonar.projectVersion=1.0
sonar.sources=hflav_fair_client
sonar.tests=tests
sonar.python.coverage.reportPaths=coverage.xml
sonar.python.version=3.8,3.9,3.10,3.11
```

You can customize these settings as needed.

### Excluding Files from Analysis

To exclude certain files or directories from analysis, add to `sonar-project.properties`:

```properties
sonar.exclusions=**/migrations/**,**/__pycache__/**,**/tests/**
```

## Analyzing Specific Files

### Using VS Code Extension

If you have the SonarQube extension installed:

1. Open the file you want to analyze
2. Right-click in the editor
3. Select "SonarQube: Analyze current file"

This is useful for:
- Quick checks during development
- Analyzing files not part of the workspace
- Checking excluded files