import React, { useState } from 'react';
import { Plus, Trash2, Save, FileUp } from 'lucide-react';
import { apiService } from '../services/api';
import type { CustomJob, CustomOperation } from '../types';

interface CustomInstanceBuilderProps {
  onInstanceCreated: () => void;
}

export const CustomInstanceBuilder: React.FC<CustomInstanceBuilderProps> = ({ onInstanceCreated }) => {
  const [instanceName, setInstanceName] = useState('');
  const [description, setDescription] = useState('');
  const [machines, setMachines] = useState<string[]>(['Machine1', 'Machine2']);
  const [jobs, setJobs] = useState<CustomJob[]>([
    {
      job_id: 'Job1',
      operations: [
        { machine: 'Machine1', duration: 5, label: 'Step 1' }
      ],
      priority: 3,
      deadline: undefined,
      release_time: 0
    }
  ]);
  const [newMachine, setNewMachine] = useState('');
  const [csvContent, setCsvContent] = useState('');
  const [showCsvImport, setShowCsvImport] = useState(false);

  const addMachine = () => {
    if (newMachine && !machines.includes(newMachine)) {
      setMachines([...machines, newMachine]);
      setNewMachine('');
    }
  };

  const removeMachine = (machine: string) => {
    setMachines(machines.filter(m => m !== machine));
  };

  const addJob = () => {
    const newJobId = `Job${jobs.length + 1}`;
    setJobs([
      ...jobs,
      {
        job_id: newJobId,
        operations: [{ machine: machines[0] || 'Machine1', duration: 5, label: 'Step 1' }],
        priority: 3,
        deadline: undefined,
        release_time: 0
      }
    ]);
  };

  const removeJob = (index: number) => {
    setJobs(jobs.filter((_, i) => i !== index));
  };

  const updateJob = (index: number, updates: Partial<CustomJob>) => {
    const newJobs = [...jobs];
    newJobs[index] = { ...newJobs[index], ...updates };
    setJobs(newJobs);
  };

  const addOperation = (jobIndex: number) => {
    const newJobs = [...jobs];
    newJobs[jobIndex].operations.push({
      machine: machines[0] || 'Machine1',
      duration: 5,
      label: `Step ${newJobs[jobIndex].operations.length + 1}`
    });
    setJobs(newJobs);
  };

  const removeOperation = (jobIndex: number, opIndex: number) => {
    const newJobs = [...jobs];
    newJobs[jobIndex].operations = newJobs[jobIndex].operations.filter((_, i) => i !== opIndex);
    setJobs(newJobs);
  };

  const updateOperation = (jobIndex: number, opIndex: number, updates: Partial<CustomOperation>) => {
    const newJobs = [...jobs];
    newJobs[jobIndex].operations[opIndex] = { ...newJobs[jobIndex].operations[opIndex], ...updates };
    setJobs(newJobs);
  };

  const handleSave = async () => {
    if (!instanceName.trim()) {
      alert('Please enter an instance name');
      return;
    }

    try {
      const response = await apiService.createCustomInstance({
        name: instanceName,
        description: description,
        jobs: jobs.map(job => ({
          job_id: job.job_id,
          operations: job.operations.map((op, idx) => ({
            op_id: idx,
            ...op
          })),
          priority: job.priority,
          deadline: job.deadline,
          release_time: job.release_time
        })),
        machines: machines
      });

      if (response.success) {
        alert(`Instance "${instanceName}" created successfully!`);
        onInstanceCreated();
        // Reset form
        setInstanceName('');
        setDescription('');
      }
    } catch (error) {
      console.error('Error creating instance:', error);
      alert('Failed to create instance');
    }
  };

  const handleCsvImport = async () => {
    try {
      const response = await apiService.importFromCsv(csvContent);
      
      if (response.success) {
        // Convert the parsed data to jobs
        const importedJobs: CustomJob[] = Object.entries(response.jobs).map(([jobId, operations]: [string, any]) => ({
          job_id: jobId,
          operations: operations.map((op: any, idx: number) => ({
            machine: op.machine,
            duration: op.duration,
            label: op.label || `Step ${idx + 1}`
          })),
          priority: 3,
          deadline: undefined,
          release_time: 0
        }));

        setJobs(importedJobs);
        setMachines(response.machines);
        setShowCsvImport(false);
        alert(response.preview);
      }
    } catch (error) {
      console.error('Error importing CSV:', error);
      alert('Failed to import CSV. Please check the format.');
    }
  };

  return (
    <div className="glass-panel p-8 max-w-6xl mx-auto animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-3xl font-bold gradient-text">Custom Instance Builder</h2>
        <button
          onClick={() => setShowCsvImport(!showCsvImport)}
          className="btn-secondary flex items-center gap-2"
        >
          <FileUp size={20} />
          Import CSV
        </button>
      </div>

      {showCsvImport && (
        <div className="mb-6 bg-white/5 p-4 rounded-xl border border-white/10">
          <h3 className="text-lg font-semibold mb-2">CSV Import</h3>
          <p className="text-sm text-white/70 mb-3">
            Format: job_id, machine, duration, label (one operation per line)
          </p>
          <textarea
            value={csvContent}
            onChange={(e) => setCsvContent(e.target.value)}
            className="input-field min-h-[120px] font-mono text-sm mb-3"
            placeholder="Job1,Machine1,5,Step 1&#10;Job1,Machine2,3,Step 2&#10;Job2,Machine1,4,Step 1"
          />
          <button onClick={handleCsvImport} className="btn-primary">
            Import
          </button>
        </div>
      )}

      <div className="space-y-6">
        {/* Basic Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Instance Name *</label>
            <input
              type="text"
              value={instanceName}
              onChange={(e) => setInstanceName(e.target.value)}
              className="input-field"
              placeholder="my_custom_instance"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Description</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="input-field"
              placeholder="Describe your scheduling problem"
            />
          </div>
        </div>

        {/* Machines */}
        <div className="bg-white/5 p-4 rounded-xl border border-white/10">
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            Machines ({machines.length})
          </h3>
          <div className="flex flex-wrap gap-2 mb-3">
            {machines.map((machine) => (
              <div key={machine} className="flex items-center gap-2 bg-white/10 px-3 py-1 rounded-lg">
                <span>{machine}</span>
                <button
                  onClick={() => removeMachine(machine)}
                  className="text-red-400 hover:text-red-300"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={newMachine}
              onChange={(e) => setNewMachine(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addMachine()}
              className="input-field flex-1"
              placeholder="New machine name"
            />
            <button onClick={addMachine} className="btn-secondary">
              <Plus size={20} />
            </button>
          </div>
        </div>

        {/* Jobs */}
        <div className="bg-white/5 p-4 rounded-xl border border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Jobs ({jobs.length})</h3>
            <button onClick={addJob} className="btn-primary flex items-center gap-2">
              <Plus size={20} />
              Add Job
            </button>
          </div>

          <div className="space-y-4">
            {jobs.map((job, jobIdx) => (
              <div key={jobIdx} className="bg-white/5 p-4 rounded-lg border border-white/10">
                <div className="flex items-start justify-between mb-3">
                  <input
                    type="text"
                    value={job.job_id}
                    onChange={(e) => updateJob(jobIdx, { job_id: e.target.value })}
                    className="input-field w-48"
                  />
                  <button
                    onClick={() => removeJob(jobIdx)}
                    className="text-red-400 hover:text-red-300"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                  <div>
                    <label className="block text-xs text-white/70 mb-1">Priority</label>
                    <select
                      value={job.priority}
                      onChange={(e) => updateJob(jobIdx, { priority: parseInt(e.target.value) })}
                      className="input-field"
                    >
                      <option value={1}>1 - Critical</option>
                      <option value={2}>2 - High</option>
                      <option value={3}>3 - Normal</option>
                      <option value={4}>4 - Low</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-white/70 mb-1">Deadline (optional)</label>
                    <input
                      type="number"
                      value={job.deadline || ''}
                      onChange={(e) => updateJob(jobIdx, { deadline: e.target.value ? parseInt(e.target.value) : undefined })}
                      className="input-field"
                      placeholder="No deadline"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-white/70 mb-1">Release Time</label>
                    <input
                      type="number"
                      value={job.release_time}
                      onChange={(e) => updateJob(jobIdx, { release_time: parseInt(e.target.value) || 0 })}
                      className="input-field"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Operations ({job.operations.length})</span>
                    <button
                      onClick={() => addOperation(jobIdx)}
                      className="text-xs btn-secondary py-1 px-3"
                    >
                      + Operation
                    </button>
                  </div>

                  {job.operations.map((op, opIdx) => (
                    <div key={opIdx} className="flex gap-2 items-center bg-white/5 p-2 rounded">
                      <span className="text-sm text-white/70 w-8">{opIdx + 1}.</span>
                      <input
                        type="text"
                        value={op.label}
                        onChange={(e) => updateOperation(jobIdx, opIdx, { label: e.target.value })}
                        className="input-field flex-1"
                        placeholder="Label"
                      />
                      <select
                        value={op.machine}
                        onChange={(e) => updateOperation(jobIdx, opIdx, { machine: e.target.value })}
                        className="input-field w-32"
                      >
                        {machines.map((m) => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                      <input
                        type="number"
                        value={op.duration}
                        onChange={(e) => updateOperation(jobIdx, opIdx, { duration: parseInt(e.target.value) || 0 })}
                        className="input-field w-20"
                        min="1"
                      />
                      <span className="text-sm text-white/70">min</span>
                      <button
                        onClick={() => removeOperation(jobIdx, opIdx)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Save Button */}
        <button onClick={handleSave} className="btn-primary w-full flex items-center justify-center gap-2 py-4 text-lg">
          <Save size={24} />
          Save Custom Instance
        </button>
      </div>
    </div>
  );
};
