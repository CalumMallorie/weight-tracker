# Setting up Weight Tracker on UnRAID

## Understanding the Permission Issue

The error `PermissionError: [Errno 13] Permission denied: '/app/logs/weight_tracker.log'` occurs because the container user doesn't have write permissions to the volume-mounted logs directory on your UnRAID host.

## Solution

### Method 1: Using the Updated Docker Compose

This repository now includes an updated `docker-compose.yml` that sets the user ID (PUID) and group ID (PGID) to match common UnRAID configurations. The Dockerfile has also been updated with an entrypoint script that handles permissions properly.

1. Clone this repository on your UnRAID server
2. Navigate to the repository directory
3. Run `docker-compose down` if you have a previous version running
4. Run `docker-compose build --no-cache` to rebuild with the new configuration
5. Run `docker-compose up -d` to start the container

### Method 2: Manual Configuration in UnRAID Docker UI

If you prefer using the UnRAID Docker UI:

1. In the UnRAID web interface, go to the "Docker" tab
2. Click "Add Container"
3. Set the repository to `calomal/weight-tracker` (or your custom image name)
4. Set a name for the container (e.g., "weight-tracker")
5. Add the following path mappings:
   - Host Path: `/path/on/unraid/data` → Container Path: `/app/data`
   - Host Path: `/path/on/unraid/logs` → Container Path: `/app/logs`
6. Add the following environment variables:
   - `PUID`: The user ID you want to run as (typically 99 for nobody on UnRAID)
   - `PGID`: The group ID you want to run as (typically 100 for users on UnRAID)
   - `PORT`: 8080
   - `LOG_LEVEL`: INFO
   - `FLASK_DEBUG`: false
7. Set the port mapping: 8080:8080
8. Click "Apply"

## WebUI Integration in UnRAID

The docker-compose.yml file now includes UnRAID-specific labels to properly display the WebUI button in the UnRAID interface:

```yaml
labels:
  - "org.opencontainers.image.title=Weight Tracker"
  - "org.opencontainers.image.description=A simple weight tracking application"
  - "org.opencontainers.image.authors=CalumMallorie"
  - "org.opencontainers.image.url=https://github.com/calummallorie/weight-tracker"
  - "io.unraid.webui=http://[IP]:[PORT:8080]"
  - "io.unraid.icon=https://raw.githubusercontent.com/calummallorie/weight-tracker/main/unraid_icon.png"
```

To manually add WebUI support when creating a container through the UnRAID interface:

1. In the "Add Container" form, scroll down to the "Extra Parameters" section
2. Add the following labels:
   - Key: `io.unraid.webui` Value: `http://[IP]:[PORT:8080]`
   - Key: `io.unraid.icon` Value: `https://raw.githubusercontent.com/calummallorie/weight-tracker/main/unraid_icon.png`

After adding these labels, a WebUI button will appear in the Docker container list, which opens the Weight Tracker application in your browser.

## About the "weight-tracker-weight-tracker" Image

When you use `docker-compose`, it automatically names images as `[directory_name]-[service_name]`. In this case, the directory is "weight-tracker" and the service name in docker-compose.yml is also "weight-tracker", resulting in the "weight-tracker-weight-tracker" image name.

To use a cleaner name, you can:

1. Set a custom image name in docker-compose.yml:
   ```yaml
   services:
     weight-tracker:
       build:
         context: .
       image: weight-tracker:latest
   ```

2. Or use `docker build` directly:
   ```bash
   docker build -t weight-tracker .
   ```

## Troubleshooting

If you still encounter permission issues:

1. Verify the host directories exist and have the correct permissions:
   ```bash
   mkdir -p /path/on/unraid/data /path/on/unraid/logs
   chmod -R 777 /path/on/unraid/data /path/on/unraid/logs
   ```
   
2. Try using a different user/group ID by modifying the PUID/PGID values

3. Check the container logs:
   ```bash
   docker logs weight-tracker
   ``` 