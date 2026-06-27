from __future__ import annotations

import math
from typing import Any


def calculate_logic_score(cpu_score: int, gpu_score: int, ram_score: int) -> int:
    logic_score = (cpu_score * 0.4) + (gpu_score * 0.5) + (ram_score * 0.1)
    return round(logic_score)


def calculate_total_price(
    cpu_price: float,
    gpu_price: float,
    mobo_price: float,
    ram_price: float,
    psu_price: float,
    case_price: float,
) -> float:
    total_price = cpu_price + gpu_price + mobo_price + ram_price + psu_price + case_price
    return round(total_price, 2)


def check_budget(total_price: float, budget: float) -> bool:
    return total_price <= budget


def detect_bottleneck(cpu_score: int, gpu_score: int) -> tuple[str, float]:
    difference = abs(cpu_score - gpu_score)
    max_score = max(cpu_score, gpu_score)
    severity = 0.0 if max_score == 0 else difference / max_score

    if cpu_score < gpu_score:
        bottleneck = 'CPU'
    else:
        bottleneck = 'GPU'

    return bottleneck, round(severity * 100, 1)


def estimate_game_performance(
    cpu_score: int,
    gpu_score: int,
    game_id: int,
    preset: str,
    game_preset_applied: list[dict[str, Any]],
) -> tuple[bool, float]:
    required_cpu = 0
    required_gpu = 0

    for row in game_preset_applied:
        if row['Game_ID'] == game_id and row['Game_Preset'].upper() == preset.upper():
            required_cpu = row['Minimum_CPU_Score']
            required_gpu = row['Minimum_GPU_Score']
            break

    playable = cpu_score >= required_cpu and gpu_score >= required_gpu

    if required_gpu == 0 and required_cpu == 0:
        return False, 0.0

    ratio = required_cpu / required_gpu if required_gpu else 1
    weight_cpu = ratio / (ratio + 1)
    weight_gpu = 1 - weight_cpu
    weight_cpu = round(weight_cpu, 1)
    weight_gpu = round(weight_gpu, 1)
    total = weight_cpu + weight_gpu
    weight_cpu = weight_cpu / total if total else 0.5
    weight_gpu = weight_gpu / total if total else 0.5

    performance_weighted = (weight_cpu * cpu_score) + (weight_gpu * gpu_score)
    performance_balance = math.sqrt(cpu_score * gpu_score)
    performance_score = (0.5 * performance_weighted) + (0.5 * performance_balance)

    return playable, round(performance_score, 1)
