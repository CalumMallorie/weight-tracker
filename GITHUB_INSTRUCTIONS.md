# GitHub Repository Setup Instructions

Follow these steps to push your Weight Tracker application to GitHub.

## Prerequisites

1. GitHub account
2. Git installed and configured on your machine

## Creating a New GitHub Repository

1. Log in to your GitHub account
2. Click the "+" button in the top right corner and select "New repository"
3. Name your repository (e.g., "weight-tracker")
4. Optionally add a description
5. Choose public or private visibility
6. Click "Create repository"

## Pushing Your Code to GitHub

Once your repository is created, GitHub will show instructions. Follow these commands:

### If you haven't already initialized the repository locally

```bash
# Initialize the repository
git init

# Add all files to staging
git add .

# Commit the files
git commit -m "Initial commit of Weight Tracker application"
```

### Add the GitHub remote and push

Replace `yourusername` with your GitHub username:

```bash
# Add the GitHub repository as a remote
git remote add origin https://github.com/yourusername/weight-tracker.git

# Push the code to GitHub
git push -u origin main
```

You might be prompted to enter your GitHub credentials.

## Setting Up GitHub Actions for Docker Hub (Optional)

You can automate the Docker build and push process using GitHub Actions.

1. Create a file at `.github/workflows/docker-build.yml` with the following content:

```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2
        
      - name: Login to DockerHub
        uses: docker/login-action@v1
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
          
      - name: Build and push
        uses: docker/build-push-action@v2
        with:
          push: true
          tags: calomal/weight-tracker:latest
```

2. In your GitHub repository settings, add these secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username (calomal)
   - `DOCKERHUB_TOKEN`: Your Docker Hub access token (generate this in Docker Hub account settings)

With this setup, every push to the main branch will automatically build and push the Docker image to Docker Hub. 