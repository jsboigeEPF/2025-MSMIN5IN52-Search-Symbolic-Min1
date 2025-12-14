"""FastAPI backend for Job-Shop Scheduling with WebSocket support."""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data import get_instances, instance_horizon, JobShopInstance
from solver import solve, SolutionResult
from visualization import operations_dataframe

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Job-Shop Scheduling API",
    description="REST API for constraint-based job shop scheduling using OR-Tools",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")

manager = ConnectionManager()

# Request/Response Models
class SolveRequest(BaseModel):
    instance_name: str = Field(..., description="Name of the instance to solve")
    time_limit: Optional[float] = Field(None, ge=0, description="Time limit in seconds")
    num_workers: int = Field(8, ge=1, le=16, description="Number of parallel workers")

class OperationResponse(BaseModel):
    job_id: str
    op_id: int
    machine: str
    start: int
    end: int
    duration: int
    label: str

class SolutionResponse(BaseModel):
    status: str
    makespan: Optional[int]
    operations: List[OperationResponse]
    solver_statistics: Dict[str, float]

class InstanceInfo(BaseModel):
    name: str
    description: str
    num_jobs: int
    num_machines: int
    num_operations: int
    horizon: int
    machines: List[str]
    has_maintenance: bool

class InstancesResponse(BaseModel):
    instances: List[InstanceInfo]
    total: int

# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "service": "Job-Shop Scheduling API",
        "version": "2.0.0"
    }

@app.get("/api/instances", response_model=InstancesResponse)
async def get_all_instances():
    """Get list of all available instances."""
    try:
        instances = get_instances()
        instance_list = []
        
        for name, instance in instances.items():
            num_ops = sum(len(job.operations) for job in instance.jobs)
            instance_list.append(InstanceInfo(
                name=name,
                description=instance.description,
                num_jobs=len(instance.jobs),
                num_machines=len(instance.machines),
                num_operations=num_ops,
                horizon=instance_horizon(instance),
                machines=instance.machines,
                has_maintenance=len(instance.maintenance) > 0
            ))
        
        return InstancesResponse(instances=instance_list, total=len(instance_list))
    except Exception as e:
        logger.error(f"Error getting instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/instances/{instance_name}")
async def get_instance_details(instance_name: str):
    """Get detailed information about a specific instance."""
    try:
        instances = get_instances()
        if instance_name not in instances:
            raise HTTPException(status_code=404, detail=f"Instance '{instance_name}' not found")
        
        instance = instances[instance_name]
        
        jobs_data = []
        for job in instance.jobs:
            operations_data = [
                {
                    "op_id": op.op_id,
                    "machine": op.machine,
                    "duration": op.duration,
                    "label": op.label
                }
                for op in job.operations
            ]
            jobs_data.append({
                "jobId": job.job_id,
                "operations": operations_data
            })
        
        maintenance_data = [
            {
                "machine": m.machine,
                "start": m.start,
                "duration": m.duration,
                "label": m.label
            }
            for m in instance.maintenance
        ]
        
        return {
            "name": instance.name,
            "description": instance.description,
            "machines": instance.machines,
            "jobs": jobs_data,
            "maintenance": maintenance_data,
            "horizon": instance_horizon(instance)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting instance details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/solve", response_model=SolutionResponse)
async def solve_instance(request: SolveRequest):
    """Solve a job shop scheduling instance."""
    try:
        logger.info(f"Solving instance: {request.instance_name}")
        
        instances = get_instances()
        if request.instance_name not in instances:
            raise HTTPException(
                status_code=404,
                detail=f"Instance '{request.instance_name}' not found"
            )
        
        instance = instances[request.instance_name]
        
        # Broadcast start message
        await manager.broadcast({
            "type": "solving_started",
            "instance": request.instance_name
        })
        
        # Solve the instance
        solution = solve(
            instance=instance,
            time_limit=request.time_limit,
            num_workers=request.num_workers
        )
        
        # Convert operations to response format
        operations = [
            OperationResponse(
                job_id=op.job_id,
                op_id=op.op_id,
                machine=op.machine,
                start=op.start,
                end=op.end,
                duration=op.duration,
                label=op.label
            )
            for op in solution.operations
        ]
        
        response = SolutionResponse(
            status=solution.status,
            makespan=solution.makespan,
            operations=operations,
            solver_statistics=solution.solver_statistics
        )
        
        # Broadcast completion
        await manager.broadcast({
            "type": "solving_completed",
            "instance": request.instance_name,
            "status": solution.status,
            "makespan": solution.makespan
        })
        
        logger.info(f"Solution completed: {solution.status}, makespan: {solution.makespan}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error solving instance: {e}")
        await manager.broadcast({
            "type": "solving_error",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/visualization/{instance_name}")
async def get_visualization_data(instance_name: str):
    """Get visualization data for a solved instance."""
    try:
        instances = get_instances()
        if instance_name not in instances:
            raise HTTPException(
                status_code=404,
                detail=f"Instance '{instance_name}' not found"
            )
        
        instance = instances[instance_name]
        solution = solve(instance=instance, time_limit=5.0, num_workers=8)
        
        df = operations_dataframe(solution, maintenance=instance.maintenance)
        
        # Convert dataframe to JSON-friendly format
        data = df.to_dict(orient="records")
        
        return {
            "data": data,
            "makespan": solution.makespan,
            "status": solution.status,
            "machines": instance.machines
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting visualization data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Custom Instance Management
import csv
import io
import httpx

# Import database module
try:
    from backend.database import db
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from database import db

class CustomInstanceRequest(BaseModel):
    name: str
    description: str
    jobs: List[dict]
    machines: List[str]
    maintenance: Optional[List[dict]] = []

@app.post("/api/instances/custom")
async def create_custom_instance(request: CustomInstanceRequest):
    """Create a new custom instance."""
    try:
        data = request.dict()
        instance_id = db.save_instance(request.name, request.description, data)
        
        # Create notification
        db.create_notification(
            "instance_created",
            f"Custom instance '{request.name}' has been created",
            {"instance_name": request.name}
        )
        
        # Broadcast to connected clients
        await manager.broadcast({
            "type": "instance_created",
            "instance_name": request.name
        })
        
        return {"success": True, "instance_id": instance_id, "name": request.name}
    except Exception as e:
        logger.error(f"Error creating custom instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/instances/custom/{instance_name}")
async def update_custom_instance(instance_name: str, request: CustomInstanceRequest):
    """Update an existing custom instance."""
    try:
        data = request.dict()
        instance_id = db.save_instance(request.name, request.description, data)
        
        db.create_notification(
            "instance_updated",
            f"Instance '{instance_name}' has been updated",
            {"instance_name": instance_name}
        )
        
        return {"success": True, "instance_id": instance_id}
    except Exception as e:
        logger.error(f"Error updating custom instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/instances/custom/{instance_name}")
async def delete_custom_instance(instance_name: str):
    """Delete a custom instance."""
    try:
        deleted = db.delete_instance(instance_name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Instance '{instance_name}' not found")
        
        db.create_notification(
            "instance_deleted",
            f"Instance '{instance_name}' has been deleted",
            {"instance_name": instance_name}
        )
        
        return {"success": True, "message": f"Instance '{instance_name}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting custom instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/instances/custom")
async def get_custom_instances():
    """Get all custom instances."""
    try:
        instances = db.get_all_instances()
        return {"instances": instances, "total": len(instances)}
    except Exception as e:
        logger.error(f"Error getting custom instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/instances/import-csv")
async def import_from_csv(csv_content: str):
    """Import instance from CSV format."""
    try:
        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content))
        jobs = {}
        machines = set()
        
        for row in reader:
            job_id = row['job_id']
            machine = row['machine']
            duration = int(row['duration'])
            label = row.get('label', f"Operation {len(jobs.get(job_id, []))}")
            
            machines.add(machine)
            if job_id not in jobs:
                jobs[job_id] = []
            jobs[job_id].append({"machine": machine, "duration": duration, "label": label})
        
        return {
            "success": True,
            "jobs": jobs,
            "machines": list(machines),
            "preview": f"Found {len(jobs)} jobs and {len(machines)} machines"
        }
    except Exception as e:
        logger.error(f"Error importing CSV: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")

# Solution History
@app.get("/api/solutions/history/{instance_name}")
async def get_solution_history(instance_name: str, limit: int = 10):
    """Get solution history for an instance."""
    try:
        history = db.get_solution_history(instance_name, limit)
        return {"history": history, "total": len(history)}
    except Exception as e:
        logger.error(f"Error getting solution history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Batch Processing
class BatchSolveRequest(BaseModel):
    instance_names: List[str]
    time_limit: Optional[float] = None
    num_workers: int = 8

@app.post("/api/batch-solve")
async def batch_solve(request: BatchSolveRequest):
    """Solve multiple instances in batch."""
    try:
        results = []
        instances = get_instances()
        
        for instance_name in request.instance_names:
            if instance_name not in instances:
                results.append({
                    "instance_name": instance_name,
                    "status": "ERROR",
                    "error": f"Instance '{instance_name}' not found"
                })
                continue
            
            instance = instances[instance_name]
            solution = solve(instance=instance, time_limit=request.time_limit, num_workers=request.num_workers)
            
            # Save to history
            db.save_solution(
                instance_name,
                solution.status,
                solution.makespan,
                [op.__dict__ for op in solution.operations],
                solution.solver_statistics
            )
            
            results.append({
                "instance_name": instance_name,
                "status": solution.status,
                "makespan": solution.makespan
            })
        
        db.create_notification(
            "batch_complete",
            f"Batch processing completed for {len(request.instance_names)} instances",
            {"results": results}
        )
        
        return {"results": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Webhook Management
class WebhookRequest(BaseModel):
    url: str
    event: str

@app.post("/api/webhooks")
async def register_webhook(request: WebhookRequest):
    """Register a webhook for events."""
    try:
        webhook_id = db.register_webhook(request.url, request.event)
        return {"success": True, "webhook_id": webhook_id}
    except Exception as e:
        logger.error(f"Error registering webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/webhooks")
async def get_webhooks():
    """Get all registered webhooks."""
    try:
        webhooks = db.get_webhooks()
        return {"webhooks": webhooks, "total": len(webhooks)}
    except Exception as e:
        logger.error(f"Error getting webhooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def trigger_webhooks(event: str, data: dict):
    """Trigger all webhooks for an event."""
    webhooks = db.get_webhooks(event)
    async with httpx.AsyncClient() as client:
        for webhook in webhooks:
            try:
                await client.post(webhook["url"], json={"event": event, "data": data})
                logger.info(f"Webhook triggered: {webhook['url']}")
            except Exception as e:
                logger.error(f"Failed to trigger webhook {webhook['url']}: {e}")

# Notifications
@app.get("/api/notifications")
async def get_notifications(unread_only: bool = False, limit: int = 50):
    """Get notifications."""
    try:
        notifications = db.get_notifications(unread_only, limit)
        return {"notifications": notifications, "total": len(notifications)}
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int):
    """Mark a notification as read."""
    try:
        updated = db.mark_notification_read(notification_id)
        if not updated:
            raise HTTPException(status_code=404, detail=f"Notification {notification_id} not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics & Reporting
@app.get("/api/analytics/bottlenecks/{instance_name}")
async def analyze_bottlenecks(instance_name: str):
    """Analyze bottlenecks in a solved instance."""
    try:
        instances = get_instances()
        if instance_name not in instances:
            raise HTTPException(status_code=404, detail=f"Instance '{instance_name}' not found")
        
        instance = instances[instance_name]
        solution = solve(instance=instance, time_limit=5.0, num_workers=8)
        
        # Analyze machine utilization
        machine_times = {}
        for op in solution.operations:
            if op.machine not in machine_times:
                machine_times[op.machine] = 0
            machine_times[op.machine] += op.duration
        
        total_time = solution.makespan if solution.makespan else max(machine_times.values())
        
        bottlenecks = []
        for machine, busy_time in machine_times.items():
            utilization = (busy_time / total_time * 100) if total_time > 0 else 0
            bottlenecks.append({
                "machine": machine,
                "busy_time": busy_time,
                "utilization_percent": round(utilization, 2),
                "is_bottleneck": utilization > 80
            })
        
        bottlenecks.sort(key=lambda x: x["utilization_percent"], reverse=True)
        
        recommendations = []
        for b in bottlenecks:
            if b["is_bottleneck"]:
                recommendations.append(f"Consider adding capacity to {b['machine']} ({b['utilization_percent']}% utilized)")
        
        return {
            "instance_name": instance_name,
            "makespan": solution.makespan,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing bottlenecks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/comparison")
async def compare_instances(instance_names: str):
    """Compare multiple instances side-by-side."""
    try:
        names = instance_names.split(",")
        instances = get_instances()
        results = []
        
        for name in names:
            name = name.strip()
            if name not in instances:
                continue
            
            instance = instances[name]
            solution = solve(instance=instance, time_limit=5.0, num_workers=8)
            
            results.append({
                "name": name,
                "makespan": solution.makespan,
                "status": solution.status,
                "num_jobs": len(instance.jobs),
                "num_machines": len(instance.machines),
                "wall_time": solution.solver_statistics.get("wall_time", 0)
            })
        
        return {"comparisons": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Error comparing instances: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
