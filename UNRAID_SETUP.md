# Setting up Weight Tracker on UnRAID

## Understanding the Permission Issues

Two common errors you might see when running the app on UnRAID:

1. `PermissionError: [Errno 13] Permission denied: '/app/logs/weight_tracker.log'` - This occurs when the container user doesn't have write permissions to the volume-mounted logs directory.

2. `PermissionError: [Errno 13] Permission denied: '/app/instance'` - This occurs when the Flask SQLAlchemy instance directory doesn't have proper permissions.

## Solution

### Method 1: Using the Updated Docker Compose

This repository now includes an updated `docker-compose.yml` that sets the user ID (PUID) and group ID (PGID) to match common UnRAID configurations. The Dockerfile has also been updated with an entrypoint script that handles permissions properly.

1. Clone this repository on your UnRAID server
2. Navigate to the repository directory
3. Run `docker-compose down` if you have a previous version running
4. Run `docker-compose build --no-cache` to rebuild with the new configuration
5. Run `docker-compose up -d` to start the container

### Method 2: Using the Docker Hub Image (Manual Setup)

If you're using the pre-built image from Docker Hub, make sure to set up these volumes and environment variables:

```bash
docker run -d \
  --name=weight-tracker \
  -p 8080:8080 \
  -v /mnt/user/appdata/weight-tracker/data:/app/data \
  -v /mnt/user/appdata/weight-tracker/logs:/app/logs \
  -v /mnt/user/appdata/weight-tracker/instance:/app/instance \
  -e PUID=99 \
  -e PGID=100 \
  -e INSTANCE_PATH=/app/instance \
  --restart unless-stopped \
  calomal/weight-tracker
```

### Method 3: Create the Directories Manually

If you're still experiencing permission issues, you can create the directories manually with proper permissions:

```bash
mkdir -p /mnt/user/appdata/weight-tracker/{data,logs,instance}
chmod -R 777 /mnt/user/appdata/weight-tracker/logs
chmod -R 777 /mnt/user/appdata/weight-tracker/instance
chown -R 99:100 /mnt/user/appdata/weight-tracker
```

## WebUI Integration

A proper UnRAID template file (`weight-tracker.xml`) has been created for easy integration with the UnRAID Docker GUI. This template includes:

- WebUI button that links to port 8080
- Custom icon for easy identification
- Proper volume mappings
- PUID and PGID environment variables for correct permissions

### To use the template:

1. In the UnRAID Docker tab, click "Add Container"
2. Click "Template Repositories" at the bottom
3. Add this GitHub repository URL
4. The template will appear in your template list
5. Fill in any required fields and click "Apply"

The WebUI button should now appear in your Docker list for easy access to the application.

## About the "weight-tracker-weight-tracker" Image

If you see an image called "weight-tracker-weight-tracker" in your Docker images list, this is because Docker Compose uses the directory name as a prefix when building images. You can safely remove this image after building the proper "calomal/weight-tracker" image. 