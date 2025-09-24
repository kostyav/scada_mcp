# SCADA-LTS MCP Server

A Model Context Protocol (MCP) server for integrating with SCADA-LTS (Supervisory Control and Data Acquisition) systems.

## Features

This MCP server provides the following capabilities for SCADA-LTS systems:

### Tools Available
- **configure_connection**: Set up connection to SCADA-LTS system
- **get_data_sources**: Retrieve all configured data sources
- **get_data_points**: Get data points (optionally filtered by data source)
- **get_point_value**: Read current value of a specific data point
- **set_point_value**: Write value to a settable data point
- **get_alarms**: Retrieve system alarms (active or all)
- **acknowledge_alarm**: Acknowledge an alarm
- **get_system_status**: Get overall system status

### Prompts Available
- **scada_system_overview**: Comprehensive system overview with optional alarm information
- **data_point_analysis**: Detailed analysis of data points for a specific data source

## Installation

1. **Install dependencies**:
```bash
pip install mcp httpx
pip install -r requirements.txt
```

2. **Make it executable**:
```bash
chmod +x scada_lts_mcp.py
```

## Configuration

### Basic Configuration
Add to your MCP client configuration (e.g., Claude Desktop config):

```json
{
  "mcpServers": {
    "scada-lts": {
      "command": "python",
      "args": ["/path/to/scada_lts_mcp.py"]
    }
  }
}
```

### Environment Variables (Optional)
You can set default connection parameters:

```bash
export SCADA_LTS_URL="http://localhost:8080/Scada-LTS"
export SCADA_LTS_USERNAME="admin"
export SCADA_LTS_PASSWORD="admin"
```

## Usage Examples

### Initial Setup
First, configure the connection to your SCADA-LTS system:

```
Use the configure_connection tool with:
- base_url: http://your-scada-server:8080/Scada-LTS
- username: your_username (optional)
- password: your_password (optional)
```

### Basic Operations

1. **Get system overview**:
   ```
   Use the scada_system_overview prompt
   ```

2. **Read data sources**:
   ```
   Use the get_data_sources tool
   ```

3. **Monitor specific data point**:
   ```
   Use get_point_value with point_id: 123
   ```

4. **Control a device**:
   ```
   Use set_point_value with point_id: 456 and value: true
   ```

5. **Check alarms**:
   ```
   Use get_alarms tool
   ```

## SCADA-LTS System Requirements

### Supported SCADA-LTS Versions
- SCADA-LTS 2.7.x and later (recommended)
- May work with earlier versions but not tested

### Required SCADA-LTS Configuration
1. **REST API enabled** (default in modern versions)
2. **CORS configured** if accessing from different domain
3. **User permissions** configured for API access

### Default SCADA-LTS Installation
If you have SCADA-LTS running locally with default settings:
- URL: `http://localhost:8080/Scada-LTS`
- Default admin credentials: `admin/admin`

## API Endpoints Used

This MCP server interacts with the following SCADA-LTS REST API endpoints:

- `POST /api/auth/login` - Authentication
- `GET /api/datasources` - Data sources
- `GET /api/datapoints` - Data points
- `GET /api/point-values/{id}/latest` - Current point values
- `POST /api/point-values/{id}/set` - Set point values
- `GET /api/alarms` - System alarms
- `POST /api/alarms/{id}/ack` - Acknowledge alarms
- `GET /api/system/status` - System status

## Security Considerations

1. **Authentication**: Use strong passwords for SCADA-LTS accounts
2. **Network Security**: Ensure SCADA-LTS is not exposed to untrusted networks
3. **HTTPS**: Use HTTPS in production environments
4. **Permissions**: Create dedicated API users with minimal required permissions

## Troubleshooting

### Common Issues

1. **Connection Failed**
   - Check SCADA-LTS is running
   - Verify URL is correct
   - Ensure REST API is enabled

2. **Authentication Failed**
   - Verify username/password
   - Check user has API permissions
   - Try guest access (no credentials)

3. **No Data Returned**
   - Check data sources are configured in SCADA-LTS
   - Verify user permissions
   - Check SCADA-LTS logs

### Debug Mode
Enable debug logging by setting:
```bash
export PYTHONPATH=/path/to/mcp
python -m logging.basicConfig --level=DEBUG scada_lts_mcp.py
```

## SCADA-LTS Resources

- **Official Repository**: https://github.com/SCADA-LTS/Scada-LTS
- **Documentation**: https://github.com/SCADA-LTS/Scada-LTS/wiki
- **YouTube Tutorials**: https://www.youtube.com/@ScadaLTS
- **Community**: GitHub Discussions and StackOverflow

## Example SCADA-LTS Setup

For testing, you can quickly set up SCADA-LTS using Docker:

```bash
# Clone the repository
git clone https://github.com/SCADA-LTS/Scada-LTS.git
cd Scada-LTS

# Build and run with Gradle
./gradlew buildRun

# Or use Docker (if available)
docker run -p 8080:8080 scadalts/scada-lts:latest
```

Then access at: http://localhost:8080/Scada-LTS

## License

This MCP server is provided as-is for interfacing with SCADA-LTS systems. 
SCADA-LTS itself is released under the GPL license.

## Contributing

To extend this MCP server:

1. Add new tools in the `list_tools()` function
2. Implement the tool logic in `call_tool()`
3. Add corresponding client methods in `ScadaLTSClient`
4. Update documentation

Common extensions might include:
- Historical data queries
- Trend analysis
- Event logging
- User management
- System configuration
- Report generation