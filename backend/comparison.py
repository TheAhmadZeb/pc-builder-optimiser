from __future__ import annotations

from typing import Any


def compare_builds(build1: dict[str, Any], build2: dict[str, Any]) -> dict[str, Any]:
    return {
        'build1': build1,
        'build2': build2,
        'cpu_models': f"{build1['cpu']['Model']} | {build2['cpu']['Model']}",
        'gpu_models': f"{build1['gpu']['Model']} | {build2['gpu']['Model']}",
        'motherboard_models': f"{build1['motherboard']['Model']} | {build2['motherboard']['Model']}",
        'ram_models': f"{build1['ram']['Model']} | {build2['ram']['Model']}",
        'psu_models': f"{build1['psu']['Model']} | {build2['psu']['Model']}",
        'cpu_scores': f"{build1['cpu']['Performance_Score']} | {build2['cpu']['Performance_Score']}",
        'gpu_scores': f"{build1['gpu']['Performance_Score']} | {build2['gpu']['Performance_Score']}",
        'ram_scores': f"{build1['ram']['Performance_Score']} | {build2['ram']['Performance_Score']}",
        'logic_scores': f"{build1['logic_score']} | {build2['logic_score']}",
        'total_prices': f"£{build1['total_price']} | £{build2['total_price']}",
        'bottlenecks': f"{build1['bottleneck']} | {build2['bottleneck']}",
        'severities': f"{build1['severity']}% | {build2['severity']}%",
    }