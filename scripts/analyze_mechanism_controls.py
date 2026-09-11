#!/usr/bin/env python3
"""Attach allocator identifiability and paired-block uncertainty to a frozen run.

Use the same sponsor data file as the benchmark. Data, manifest and strategy
hashes must match its recorded context. No weights or promotion gates change.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import xarray as xr
from research.benchmark import ROOT, load_module, panel_hash
from research.iteration import load_manifest, write_json
from research.mechanism_diagnostics import allocation_difference, paired_block_interval
from research.preregister import sha256_file


def analyze(manifest_path, run_path, data_path, plan_path):
    manifest = load_manifest(manifest_path)
    context = json.loads((run_path / 'context.json').read_text())
    if sha256_file(manifest_path) != context['manifest_sha256']:
        raise ValueError('manifest does not match observed run')
    plan = json.loads(plan_path.read_text())
    if plan['campaign'] != manifest['campaign']:
        raise ValueError('analysis plan belongs to another campaign')
    data = xr.load_dataarray(data_path)
    if panel_hash(data) != context['data_sha256']:
        raise ValueError('data do not match observed run')
    jobs = {c['id']: c for c in manifest['candidates']}
    target_cache = {}

    def targets(job):
        if sha256_file(ROOT / job['path']) != context['source_hashes'][job['path']]:
            raise ValueError('strategy source changed since observed run')
        if job['id'] not in target_cache:
            m = load_module(ROOT / job['path'])
            target_cache[job['id']] = m.strategy(data, job['params'], job['mode'])
        return target_cache[job['id']]

    output = dict(campaign=manifest['campaign'], data_sha256=context['data_sha256'],
                  analysis_plan_sha256=sha256_file(plan_path),
                  diagnostics_source_sha256=sha256_file(ROOT/'research/mechanism_diagnostics.py'),
                  script_sha256=sha256_file(Path(__file__)), pairs=[])
    settings = plan['secondary_diagnostics']
    for control in manifest['candidates']:
        if control['mode'] not in ('ablation', 'falsifier'):
            continue
        parent = jobs[control['parent_id']]
        row = dict(parent=parent['id'], control=control['id'],
                   allocation=allocation_difference(targets(parent), targets(control)))
        parent_record = json.loads((run_path / (parent['id'] + '.json')).read_text())
        child_record = json.loads((run_path / (control['id'] + '.json')).read_text())
        if parent_record['status'] != 'COMPLETE' or child_record['status'] != 'COMPLETE':
            row['return_uncertainty'] = dict(status='PENDING_INVALID_RETURN_STREAM')
        else:
            p = pd.read_csv(run_path / (parent['id'] + '_returns.csv'), index_col=0, parse_dates=True)['dev'].dropna()
            c = pd.read_csv(run_path / (control['id'] + '_returns.csv'), index_col=0, parse_dates=True)['dev'].dropna()
            row['return_uncertainty'] = paired_block_interval(p, c,
                block_days=settings['block_days'], replicates=settings['bootstrap_replicates'], seed=settings['seed'])
        output['pairs'].append(row)
    write_json(run_path / 'mechanism_diagnostics.json', output)
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--run', required=True, type=Path)
    parser.add_argument('--data', required=True, type=Path)
    parser.add_argument('--plan', required=True, type=Path)
    args = parser.parse_args()
    result = analyze(args.manifest, args.run, args.data, args.plan)
    print(json.dumps(result, indent=2))
