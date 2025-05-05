# Docker Build and Push Instructions

Once you have Docker Desktop running on your machine, follow these steps to build and push the Weight Tracker application to your Docker Hub repository.

## Prerequisites

1. Docker Desktop installed and running
2. Docker Hub account (you've mentioned your repository is `calomal/weight-tracker`)
3. Logged in to Docker Hub from your terminal

## Building and Pushing the Image

### 1. Login to Docker Hub

```bash
docker login
```

Enter your Docker Hub username (`calomal`) and password when prompted.

### 2. Build the Docker Image

```bash
docker build -t calomal/weight-tracker .
```

This command builds the Docker image and tags it with your repository name.

### 3. Push the Image to Docker Hub

```bash
docker push calomal/weight-tracker
```

This uploads your image to Docker Hub, making it available for deployment on Unraid or any other system that can pull Docker images.

## Testing the Image Locally (Optional)

Before pushing, you can test the image locally:

```bash
mkdir -p data
docker run -d -p 8080:8080 -v $(pwd)/data:/app/data --name weight-tracker calomal/weight-tracker
```

Then visit `http://localhost:8080` in your browser to verify that the application works correctly.

## Using on Unraid

Once your image is pushed to Docker Hub, you can easily deploy it on Unraid:

1. In the Unraid web interface, go to the "Docker" tab
2. Click "Add Container"
3. Enter `calomal/weight-tracker` as the Repository
4. Configure the port mapping (8080:8080)
5. Add a volume mapping from `/mnt/user/appdata/weight-tracker` to `/app/data`
6. Click "Apply"

Your Weight Tracker application will be pulled from Docker Hub and started on your Unraid server. 