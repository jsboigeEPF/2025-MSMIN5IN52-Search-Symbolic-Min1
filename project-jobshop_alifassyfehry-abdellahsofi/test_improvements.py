#!/usr/bin/env python3
"""
Quick test script to validate the improved Job-Shop Scheduling implementation.
Run this to verify all improvements are working correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_data_module():
    """Test data module improvements."""
    print("Testing data module...")
    from data import get_instances, instance_horizon
    
    instances = get_instances()
    assert len(instances) > 0, "Should have instances"
    
    for name, instance in instances.items():
        print(f"  ✓ Instance '{name}': {len(instance.jobs)} jobs, {len(instance.machines)} machines")
        horizon = instance_horizon(instance)
        assert horizon > 0, f"Horizon should be positive for {name}"
    
    print("✅ Data module tests passed\n")

def test_model_module():
    """Test model building."""
    print("Testing model module...")
    from data import get_instances
    from model import build_cp_model
    
    instances = get_instances()
    instance = instances["preparation_commandes"]
    
    model_data = build_cp_model(instance)
    assert model_data is not None, "Model should be built"
    assert model_data.model is not None, "CP model should exist"
    assert model_data.makespan is not None, "Makespan variable should exist"
    assert len(model_data.task_vars) > 0, "Should have task variables"
    
    print(f"  ✓ Built model with {len(model_data.task_vars)} task variables")
    print("✅ Model module tests passed\n")

def test_solver_module():
    """Test solver functionality."""
    print("Testing solver module...")
    from data import get_instances
    from solver import solve
    
    instances = get_instances()
    instance = instances["preparation_commandes"]
    
    # Quick solve with short time limit
    solution = solve(instance, time_limit=2.0, num_workers=4)
    
    assert solution is not None, "Should return a solution"
    assert solution.status in ["OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNKNOWN"], "Should have valid status"
    print(f"  ✓ Solver status: {solution.status}")
    
    if solution.makespan:
        print(f"  ✓ Makespan: {solution.makespan}")
        print(f"  ✓ Operations scheduled: {len(solution.operations)}")
    
    print("✅ Solver module tests passed\n")

def test_visualization_module():
    """Test visualization functionality."""
    print("Testing visualization module...")
    from data import get_instances
    from solver import solve
    from visualization import operations_dataframe, gantt_figure
    
    instances = get_instances()
    instance = instances["preparation_commandes"]
    solution = solve(instance, time_limit=2.0, num_workers=4)
    
    # Test dataframe creation
    df = operations_dataframe(solution)
    assert df is not None, "Should create dataframe"
    
    if solution.makespan:
        assert len(df) > 0, "Should have operations in dataframe"
        print(f"  ✓ Created dataframe with {len(df)} rows")
        
        # Test figure creation
        fig = gantt_figure(solution)
        assert fig is not None, "Should create Gantt figure"
        print(f"  ✓ Created Gantt chart")
    
    print("✅ Visualization module tests passed\n")

def test_error_handling():
    """Test error handling improvements."""
    print("Testing error handling...")
    from solver import solve
    from data import JobShopInstance, Job
    
    # Test with invalid parameters
    try:
        from data import get_instances
        instance = get_instances()["preparation_commandes"]
        result = solve(instance, num_workers=-1)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  ✓ Caught invalid num_workers: {e}")
    
    try:
        result = solve(instance, time_limit=-5)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"  ✓ Caught invalid time_limit: {e}")
    
    print("✅ Error handling tests passed\n")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Job-Shop Scheduling - Code Improvements Validation")
    print("=" * 60 + "\n")
    
    try:
        test_data_module()
        test_model_module()
        test_solver_module()
        test_visualization_module()
        test_error_handling()
        
        print("=" * 60)
        print("🎉 All tests passed! Improvements are working correctly.")
        print("=" * 60)
        return 0
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
