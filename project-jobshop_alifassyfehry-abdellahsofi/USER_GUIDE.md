# 🎯 Job-Shop Scheduler - User Guide

## Introduction

The Job-Shop Scheduler is a powerful constraint programming application that helps optimize manufacturing schedules by minimizing makespan (total completion time) while respecting operational constraints.

## Getting Started

### 1. Launch the Application

```bash
./setup.sh
```

Or manually:
```bash
docker compose up --build
```

### 2. Access the Interface

Open your browser to: http://localhost:3000

## Using the Scheduler

### Step 1: Select an Instance

Choose from predefined scenarios:

- **🏭 Baseline: Normal Flow** - Standard order preparation
- **🔧 Maintenance Scenario** - With planned maintenance windows
- **⚡ Rush Order** - Priority rush order insertion
- **📚 Educational 3x3** - Simple learning example
- **🔄 Alternating 3x3** - Alternative machine sequences

### Step 2: Configure Solver

Adjust solver parameters:

**Time Limit**
- Set to `0` for unlimited solving time
- Recommended: `5-10` seconds for quick results
- Higher values: Better solutions but longer wait

**Parallel Workers**
- Range: 1-16 workers
- More workers = faster solving (up to CPU limit)
- Recommended: 8 workers for balanced performance

### Step 3: Solve

Click **"Solve Instance"** to start the optimization.

Watch the real-time progress indicator in the bottom-right corner.

### Step 4: Analyze Results

#### Solution Status
- **OPTIMAL**: Found the best possible solution
- **FEASIBLE**: Found a valid solution (may not be optimal)
- **INFEASIBLE**: No solution exists with given constraints

#### Key Metrics

**Makespan**: Total time to complete all jobs (minimize this!)

**Solve Time**: How long the solver took

**Conflicts**: Number of search conflicts (higher = harder problem)

**Branches**: Search tree branches explored

**Best Bound**: Lower bound on optimal solution

#### Gantt Chart

Visual timeline showing:
- Each job color-coded
- Operations scheduled on machines
- Maintenance windows (gray)
- Makespan line (red dashed)

**Hover** over operations for details.

## Understanding Instances

### Instance Details Section

Shows:
- **Resources/Machines**: Available equipment
- **Jobs**: Orders to process with operations
- **Maintenance Windows**: Scheduled downtime

### Example: Preparation Orders

A typical e-commerce fulfillment scenario:

**Resources:**
- Station de picking (Picking station)
- Cellule d'emballage (Packaging cell)
- Imprimante etiquette (Label printer)

**Jobs:**
- Order #A12: Pick → Pack → Label
- Order #B07: Pick → Print → Package
- Order #C21: Print → Pick → Pack

**Constraints:**
- Each operation must complete before the next starts
- Machines can only handle one operation at a time
- Maintenance windows block machine availability

## Tips for Best Results

### 🎯 Problem Selection
- Start with simpler instances (3x3) to understand behavior
- Progress to realistic scenarios (maintenance, rush orders)

### ⚙️ Solver Configuration
- Short time limits (2-5s) for quick exploration
- Longer limits (10-30s) for better solutions
- More workers help on complex instances

### 📊 Solution Analysis
- Compare different scenarios to see constraint impact
- Check machine utilization for bottlenecks
- Look at conflicts/branches to gauge problem difficulty

### 🔧 Optimization Strategies

1. **Minimize Makespan**: Primary goal
2. **Balance Load**: Avoid machine bottlenecks
3. **Consider Maintenance**: Schedule around downtime
4. **Handle Rush Orders**: Prioritize urgent jobs

## API Usage

### REST API

Access the backend directly at http://localhost:8000

**Get all instances:**
```bash
curl http://localhost:8000/api/instances
```

**Solve an instance:**
```bash
curl -X POST http://localhost:8000/api/solve \
  -H "Content-Type: application/json" \
  -d '{
    "instance_name": "preparation_commandes",
    "time_limit": 10,
    "num_workers": 8
  }'
```

**API Documentation:**
Interactive docs at http://localhost:8000/docs

### WebSocket

Connect to `ws://localhost:8000/ws` for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Solver update:', message);
};
```

## Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker info

# View logs
docker compose logs -f

# Restart services
docker compose down
docker compose up --build
```

### Frontend can't connect to backend

- Verify backend is running: http://localhost:8000
- Check CORS settings in `backend/main.py`
- Ensure ports 3000 and 8000 are available

### Solver takes too long

- Reduce time limit
- Try simpler instance
- Increase number of workers

### Browser issues

- Clear cache and reload
- Try different browser
- Check console for errors (F12)

## Technical Details

### Architecture

```
┌─────────────┐     HTTP/WS      ┌─────────────┐
│   React     │ ←──────────────→ │   FastAPI   │
│  Frontend   │                  │   Backend   │
│ (Port 3000) │                  │ (Port 8000) │
└─────────────┘                  └──────┬──────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │  OR-Tools    │
                                 │   CP-SAT     │
                                 └──────────────┘
```

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- Tailwind CSS for styling
- Zustand for state management
- Axios for API calls
- Custom SVG Gantt charts

**Backend:**
- FastAPI (Python 3.11)
- OR-Tools 9.9 (CP-SAT solver)
- WebSocket support
- Async/await patterns

**DevOps:**
- Docker & Docker Compose
- Hot reload for development
- Health checks
- Network isolation

## Advanced Usage

### Custom Instances

Edit `src/data.py` to add new instances:

```python
custom = _make_instance(
    name="my_scenario",
    job_sequences={
        "Job A": [("Machine1", 5), ("Machine2", 3)],
        "Job B": [("Machine2", 4), ("Machine1", 2)],
    },
    description="My custom scenario",
)
```

Restart backend to see changes.

### Modify Frontend

Edit files in `frontend/src/`:
- `components/` - React components
- `services/api.ts` - API integration
- `store/useStore.ts` - State management

Changes hot-reload automatically.

### Extend Backend

Add endpoints in `backend/main.py`:
- New algorithms
- Export formats
- Statistics endpoints

## Support

For issues, questions, or contributions:
- Check logs: `docker compose logs`
- Review API docs: http://localhost:8000/docs
- Inspect network: Browser DevTools (F12)

## License

See LICENSE file for details.

---

**Happy Scheduling! 🚀**
