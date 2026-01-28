# Sample Inputs for Postman

Use these JSON payloads to test the `POST http://127.0.0.1:8000/analyze` endpoint.

## Scenario 1: Symbolic Root Cause Found (Database Failure)
**Logic**: The system detects "Database Connection Failed" followed by "API Error 500".

```json
{
  "logs": [
    {
      "timestamp": "2023-10-27T10:00:00", 
      "level": "INFO", 
      "service": "db-service", 
      "message": "Database connection initiated"
    },
    {
      "timestamp": "2023-10-27T10:05:00", 
      "level": "ERROR", 
      "service": "db-service", 
      "message": "Database Connection Failed: Timeout"
    },
    {
      "timestamp": "2023-10-27T10:07:00", 
      "level": "ERROR", 
      "service": "api-service", 
      "message": "API Error 500: Unable to fetch user data"
    }
  ],
  "alerts": []
}
```

## Scenario 2: Neural Clustering (Pattern Detection)
**Logic**: No symbolic rules match. The system clusters the logs to find anomalies or common patterns.

```json
{
  "logs": [
    {
      "timestamp": "2023-10-27T10:00:00", "level": "INFO", "service": "auth", "message": "User login successful"
    },
    {
      "timestamp": "2023-10-27T10:01:00", "level": "WARN", "service": "auth", "message": "Token expiry warning"
    },
    {
      "timestamp": "2023-10-27T10:02:00", "level": "WARN", "service": "auth", "message": "Token expiry warning"
    },
    {
      "timestamp": "2023-10-27T10:03:00", "level": "INFO", "service": "payment", "message": "Transaction started"
    },
    {
      "timestamp": "2023-10-27T10:04:00", "level": "ERROR", "service": "payment", "message": "Payment gateway timeout 504"
    },
    {
      "timestamp": "2023-10-27T10:04:05", "level": "ERROR", "service": "payment", "message": "Payment gateway timeout 504"
    },
    {
      "timestamp": "2023-10-27T10:04:10", "level": "ERROR", "service": "payment", "message": "Payment gateway timeout 504"
    }
  ],
  "alerts": []
}
```

## Scenario 3: Deployment Triggering CPU Spike
**Logic**: Symbolic rule `Deployment Started -> High CPU Usage`.

```json
{
  "logs": [
    {
      "timestamp": "2023-11-01T14:00:00", 
      "level": "INFO", 
      "service": "deploy-service", 
      "message": "Starting rolling update for version v2.5"
    },
    {
      "timestamp": "2023-11-01T14:02:00", 
      "level": "WARN", 
      "service": "compute-service", 
      "message": "CPU utilization reached 85%"
    },
    {
      "timestamp": "2023-11-01T14:03:00", 
      "level": "ERROR", 
      "service": "compute-service", 
      "message": "High CPU usage spike detected: 99%"
    }
  ],
  "alerts": []
}
```

## Scenario 4: Single Log Entry (Testing Small Batches)
**Logic**: Tests that the neural clusterer doesn't crash on small inputs.

```json
{
  "logs": [
    {
      "timestamp": "2026-01-27T12:42:58.684Z",
      "level": "INFO",
      "service": "test-service",
      "message": "This is a single log entry for testing clustering"
    }
  ],
  "alerts": []
}
```
