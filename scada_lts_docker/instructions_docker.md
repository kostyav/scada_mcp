# SCADA-LTS Docker Setup Guide: Complete Step-by-Step Tutorial

This guide will help you set up and run a SCADA-LTS (Supervisory Control and Data Acquisition) system using Docker containers from scratch.

## Overview

SCADA-LTS is an open-source, web-based, multi-platform solution for building SCADA systems. It's used for:

- Energy management
- Water distribution monitoring
- Manufacturing plant control
- Home automation
- Laboratory monitoring
- Industrial process control

## Prerequisites

### System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: At least 2GB free space
- **Network**: Internet connection for downloading Docker images

### Software Requirements

1. **Docker Desktop** (includes Docker Engine and Docker Compose)
2. **Web browser** (Chrome, Firefox, Safari, or Edge)

## Step 1: Install Docker Desktop

### For Windows:

1. Download Docker Desktop from [https://docs.docker.com/desktop/install/windows/](https://docs.docker.com/desktop/install/windows/)
2. Run the installer and follow the setup wizard
3. Restart your computer when prompted
4. Enable virtualization in BIOS if not already enabled:
   - Restart and enter BIOS settings
   - Look for "Intel VT-x" or "AMD-V" virtualization
   - Enable it and save changes

### For macOS:

1. Download Docker Desktop from [https://docs.docker.com/desktop/install/mac/](https://docs.docker.com/desktop/install/mac/)
2. Drag Docker.app to Applications folder
3. Launch Docker Desktop from Applications

### For Linux:

1. Follow the installation guide at [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)
2. Install Docker Compose: `sudo apt-get install docker-compose-plugin`

### Verify Installation:

Open a terminal/command prompt and run:

```bash
docker --version
docker-compose --version
```

## Step 2: Create Project Directory

Create a new directory for your SCADA-LTS project:

```bash
mkdir scada-lts-docker
cd scada-lts-docker
```

## Step 3: Create Docker Compose Configuration

Download docker-compose.yaml from https://github.com/SCADA-LTS/Scada-LTS/blob/develop/docker-compose.yml

For MacOS add the following lines:

image: mysql:8.0

platform: linux/amd64

command: --innodb-use-native-aio=0 --explicit_defaults_for_timestamp=1

<!--
Create a `docker-compose.yml` file in your project directory with the following content:

```yaml
version: "3.8"

services:
  database:
    image: mysql:5.7
    container_name: scadalts_database
    restart: unless-stopped
    environment:
      MYSQL_DATABASE: scadalts
      MYSQL_USER: scadalts
      MYSQL_PASSWORD: scadalts
      MYSQL_ROOT_PASSWORD: root
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  scadalts:
    image: scadalts/scadalts:latest
    container_name: scadalts_app
    restart: unless-stopped
    ports:
      - "8080:8080"
      - "8000:8000" # Debug port (optional)
    depends_on:
      database:
        condition: service_healthy
    environment:
      - CATALINA_OPTS=-Xms512m -Xmx1024m
    # Uncomment for device access (Linux/macOS only)
    # devices:
    #   - "/dev/:/dev/"

volumes:
  mysql_data:
    driver: local
``` -->

## Step 4: Start the SCADA-LTS Environment

### Option A: Start All Services Together

```bash
docker-compose up -d
```

### Option B: Start Services Separately (Recommended)

This approach ensures the database is fully ready before starting the application:

1. **Start the database first:**

```bash
docker-compose up -d database
```

2. **Wait for database to be ready (about 30-60 seconds), then start SCADA-LTS:**

```bash
docker-compose up -d scadalts
```

### Monitor the startup process:

```bash
docker-compose logs -f scadalts
```

## Step 5: Access SCADA-LTS Web Interface

1. **Open your web browser**
2. **Navigate to:** `http://localhost:8080/Scada-LTS`
3. **Login with default credentials:**
   - Username: `admin`
   - Password: `admin`

## Step 6: Verify Installation

### Check Container Status:

```bash
docker-compose ps
```

You should see both containers running:

- `scadalts_database` (port 3306)
- `scadalts_app` (ports 8080, 8000)

### Check Application Logs:

```bash
# View SCADA-LTS logs
docker-compose logs scadalts

# View database logs
docker-compose logs database
```

## Common Operations

### Stop the Environment:

```bash
docker-compose stop
```

### Restart the Environment:

```bash
docker-compose restart
```

### Update to Latest Version:

```bash
docker-compose pull
docker-compose up -d
```

### Remove Everything (including data):

```bash
docker-compose down -v
```

### Access Container Shell:

```bash
# Access SCADA-LTS container
docker exec -it scadalts_app bash

# Access database container
docker exec -it scadalts_database mysql -u root -p
```

## Troubleshooting

### Issue 1: HTTP 404 Error - "Not Found" (Most Common)

**Symptoms:** Browser shows "HTTP Status 404 – Not Found" when accessing `http://localhost:8080/Scada-LTS`
**Root Cause:** SCADA-LTS application is still starting up or failed to deploy properly

**Diagnostic Steps:**

1. **Check container status:**

```bash
docker-compose ps
```

2. **Monitor SCADA-LTS startup logs:**

```bash
docker-compose logs -f scadalts
```

3. **Check if application is deployed:**

```bash
docker exec -it scadalts_app ls -la /usr/local/tomcat/webapps/
```

**Solutions:**

**A. Wait for Complete Startup (Most Common Fix):**

- SCADA-LTS can take 2-5 minutes to fully start
- Watch the logs until you see: `Server startup in [X] milliseconds`
- Look for: `INFO [main] org.apache.catalina.startup.Catalina.start Server startup`

**B. If WAR file is missing or not deployed:**

```bash
# Check if Scada-LTS.war exists and is deployed
docker exec -it scadalts_app ls -la /usr/local/tomcat/webapps/Scada-LTS/
```

**C. Force restart with proper timing:**

```bash
docker-compose down
docker-compose up -d database
echo "Waiting for database to be ready..."
sleep 60
docker-compose up -d scadalts
echo "Waiting for SCADA-LTS to start..."
sleep 120
```

**D. Try alternative access URLs:**

- `http://localhost:8080/` (root Tomcat page)
- `http://127.0.0.1:8080/Scada-LTS`
- `http://localhost:8080/scada-lts` (lowercase)

### Issue 2: SCADA-LTS Can't Connect to Database

**Symptoms:** Application shows database connection errors in logs
**Solution:**

1. Ensure database container is fully started before SCADA-LTS
2. Check database health: `docker-compose logs database`
3. Restart with proper order: `docker-compose down && docker-compose up -d database && sleep 30 && docker-compose up -d scadalts`

### Issue 2: Port Already in Use

**Symptoms:** Error "Port 8080 is already allocated"
**Solution:**

1. Stop conflicting services: `sudo lsof -i :8080` (Linux/macOS)
2. Change port in docker-compose.yml: `"8081:8080"`

### Issue 3: Container Won't Start

**Symptoms:** Container exits immediately
**Solution:**

1. Check logs: `docker-compose logs [service_name]`
2. Verify Docker Desktop is running
3. Ensure sufficient system resources (RAM/disk space)

### Issue 4: Can't Access Web Interface

**Symptoms:** Browser shows "connection refused" or timeout
**Solution:**

1. Verify containers are running: `docker-compose ps`
2. Check if port is correctly mapped: `docker port scadalts_app`
3. Try: `http://127.0.0.1:8080/Scada-LTS` instead of localhost

## Production Considerations

⚠️ **Important:** This setup is for development/testing only. For production:

1. **Use persistent volumes** for data storage
2. **Change default passwords** immediately
3. **Configure SSL/HTTPS** for secure access
4. **Set up proper backup** procedures
5. **Monitor system resources** and logs
6. **Use specific version tags** instead of "latest"

## Next Steps

After successful installation:

1. **Explore the interface** - Navigate through different sections
2. **Set up data sources** - Configure communication protocols
3. **Create data points** - Define what data to collect
4. **Design HMI screens** - Build graphical interfaces
5. **Configure alarms** - Set up alerts and notifications
6. **Review documentation** - Visit [SCADA-LTS Wiki](https://github.com/SCADA-LTS/Scada-LTS/wiki)

## Additional Resources

- **Official Documentation:** [SCADA-LTS GitHub Wiki](https://github.com/SCADA-LTS/Scada-LTS/wiki)
- **Docker Hub:** [SCADA-LTS Docker Images](https://hub.docker.com/r/scadalts/scadalts)
- **YouTube Tutorials:** [SCADA-LTS Channel](https://www.youtube.com/@ScadaLTS)
- **Community Support:** [GitHub Discussions](https://github.com/SCADA-LTS/Scada-LTS/discussions)
- **Official Website:** [http://scada-lts.com](http://scada-lts.com)

## Version Information

- **SCADA-LTS Version:** Latest stable release
- **Database:** MySQL 5.7
- **Java Runtime:** OpenJDK (included in container)
- **Web Server:** Apache Tomcat (included in container)

---

**Note:** The development team does not recommend using docker in a production environment without proper configuration of persistent volumes and security measures.
