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

### Method 3: Using the XML Template (Recommended for UnRAID)

The repository now includes a proper XML template for UnRAID:

1. Download the `weight-tracker.xml` file from this repository
2. In UnRAID, go to the Docker tab and click "Add Container"
3. At the bottom of the form, click "Upload" and select the `weight-tracker.xml` file
4. Review the settings and adjust paths if needed
5. Click "Apply"

## WebUI Integration in UnRAID

The proper way to have a WebUI button in UnRAID is through the XML template, which is now included in the repository. When using the template, the WebUI button will automatically appear.

If you're using docker-compose or creating the container manually, UnRAID will recognize the WebUI through the following label:

```yaml
labels:
  - "com.unraid.template.webui=http://[IP]:[PORT:8080]/"
  - "com.unraid.template.icon=https://raw.githubusercontent.com/CalumMallorie/weight-tracker/main/unraid_icon.png"
```

The WebUI button will appear in the Docker container list and open the Weight Tracker application in your browser.

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