from __future__ import annotations

from typing import Any

from backend.compatibility import check_compatibility
from backend.scoring import (
    calculate_logic_score,
    calculate_total_price,
    detect_bottleneck,
    estimate_game_performance,
)

BuildDict = dict[str, Any]


def _serialise_build(
    cpu: dict[str, Any],
    gpu: dict[str, Any],
    motherboard: dict[str, Any],
    ram: dict[str, Any],
    psu: dict[str, Any],
    logic_score: int,
    total_price: float,
    total_power: int,
) -> BuildDict:
    bottleneck, severity = detect_bottleneck(cpu['Performance_Score'], gpu['Performance_Score'])
    return {
        'cpu': cpu,
        'gpu': gpu,
        'motherboard': motherboard,
        'ram': ram,
        'psu': psu,
        'logic_score': logic_score,
        'total_price': total_price,
        'total_power_draw': total_power,
        'bottleneck': bottleneck,
        'severity': severity,
    }


def optimise_build(
    cpu_list: list[dict[str, Any]],
    gpu_list: list[dict[str, Any]],
    mobo_list: list[dict[str, Any]],
    ram_list: list[dict[str, Any]],
    psu_list: list[dict[str, Any]],
    game_presets: list[dict[str, Any]],
    budget: float,
    game_id: int,
    preset: str,
) -> list[BuildDict]:
    unique_pair_builds: list[BuildDict] = []

    cpu_list = sorted(cpu_list, key=lambda x: x['Performance_Score'], reverse=True)
    gpu_list = sorted(gpu_list, key=lambda x: x['Performance_Score'], reverse=True)
    mobo_list = sorted(mobo_list, key=lambda x: x['Price'])
    ram_list = sorted(ram_list, key=lambda x: x['Price'])
    psu_list = sorted(psu_list, key=lambda x: x['Price'])

    for cpu in cpu_list:
        compatible_mobos = [m for m in mobo_list if m['Socket_Type'] == cpu['Socket_Type']]
        if not compatible_mobos:
            continue

        for gpu in gpu_list:
            playable, _preset_score = estimate_game_performance(
                cpu['Performance_Score'],
                gpu['Performance_Score'],
                game_id,
                preset,
                game_presets,
            )
            if not playable:
                continue

            total_power = cpu['Power_Draw'] + gpu['Power_Draw']
            viable_psus = [p for p in psu_list if p['Wattage'] >= total_power]
            if not viable_psus:
                continue

            best_candidate_for_pair: BuildDict | None = None

            for motherboard in compatible_mobos:
                compatible_ram = [r for r in ram_list if r['RAM_Type'] == motherboard['RAM_Type']]
                if not compatible_ram:
                    continue

                for ram in compatible_ram:
                    logic_score = calculate_logic_score(
                        cpu['Performance_Score'],
                        gpu['Performance_Score'],
                        ram['Performance_Score'],
                    )

                    for psu in viable_psus:
                        total_price = calculate_total_price(
                            cpu['Price'],
                            gpu['Price'],
                            motherboard['Price'],
                            ram['Price'],
                            psu['Price'],
                            0,
                        )

                        if total_price > budget:
                            continue

                        compatible, _message = check_compatibility(
                            cpu,
                            gpu,
                            motherboard,
                            ram,
                            psu,
                            total_power,
                        )
                        if not compatible:
                            continue

                        candidate = _serialise_build(
                            cpu,
                            gpu,
                            motherboard,
                            ram,
                            psu,
                            logic_score,
                            total_price,
                            total_power,
                        )

                        if best_candidate_for_pair is None:
                            best_candidate_for_pair = candidate
                        else:
                            current_key = (candidate['logic_score'], -candidate['total_price'])
                            best_key = (best_candidate_for_pair['logic_score'], -best_candidate_for_pair['total_price'])
                            if current_key > best_key:
                                best_candidate_for_pair = candidate

            if best_candidate_for_pair is not None:
                unique_pair_builds.append(best_candidate_for_pair)

    unique_pair_builds.sort(
        key=lambda build: (build['logic_score'], -build['total_price']),
        reverse=True,
    )

    return unique_pair_builds[:6]


def _upgrade_item(component_type: str, component: dict[str, Any]) -> dict[str, Any]:
    return {
        'type': component_type,
        'component': component,
    }


def _find_required_psu(
    psu_list: list[dict[str, Any]],
    required_wattage: int,
    budget_remaining: float,
) -> dict[str, Any] | None:
    suitable = [
        psu for psu in psu_list
        if psu['Wattage'] >= required_wattage and psu['Price'] <= budget_remaining
    ]
    if not suitable:
        return None

    suitable.sort(key=lambda psu: (psu['Price'], psu['Wattage']))
    return suitable[0]


def recommend_upgrade(
    existing_build: dict[str, Any],
    budget: float,
    cpu_list: list[dict[str, Any]],
    gpu_list: list[dict[str, Any]],
    ram_list: list[dict[str, Any]],
    psu_list: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return the best upgrade packages by Logic Score improvement only.

    Game/preset requirements are intentionally not used here. The result set is
    also deduplicated so the same final CPU + GPU combination appears only once.
    """
    current_score = calculate_logic_score(
        existing_build['CPU_Score'],
        existing_build['GPU_Score'],
        existing_build['RAM_Score'],
    )

    current_cpu = {
        'CPU_ID': existing_build['CPU_ID'],
        'Model': existing_build['CPU_Model'],
        'Socket_Type': existing_build['Socket_Type'],
        'Power_Draw': existing_build['CPU_Power_Draw'],
        'Performance_Score': existing_build['CPU_Score'],
        'Price': 0,
        '_is_current': True,
    }
    current_gpu = {
        'GPU_ID': existing_build['GPU_ID'],
        'Model': existing_build['GPU_Model'],
        'Power_Draw': existing_build['GPU_Power_Draw'],
        'Performance_Score': existing_build['GPU_Score'],
        'Price': 0,
        '_is_current': True,
    }
    current_ram = {
        'RAM_ID': existing_build['RAM_ID'],
        'Model': existing_build['RAM_Model'],
        'RAM_Type': existing_build['RAM_Type'],
        'Performance_Score': existing_build['RAM_Score'],
        'Price': 0,
        '_is_current': True,
    }

    psu_list = sorted(psu_list or [], key=lambda psu: (psu['Price'], psu['Wattage']))
    current_psu_wattage = existing_build['PSU_Wattage']

    cpu_options = [current_cpu] + [
        cpu for cpu in cpu_list
        if cpu['Socket_Type'] == existing_build['Socket_Type']
        and cpu['Performance_Score'] > existing_build['CPU_Score']
        and cpu['Price'] <= budget
    ]
    gpu_options = [current_gpu] + [
        gpu for gpu in gpu_list
        if gpu['Performance_Score'] > existing_build['GPU_Score']
        and gpu['Price'] <= budget
    ]
    ram_options = [current_ram] + [
        ram for ram in ram_list
        if ram['RAM_Type'] == existing_build['RAM_Type']
        and ram['Performance_Score'] > existing_build['RAM_Score']
        and ram['Price'] <= budget
    ]

    cpu_options.sort(key=lambda cpu: (cpu['Performance_Score'], -cpu['Price']), reverse=True)
    gpu_options.sort(key=lambda gpu: (gpu['Performance_Score'], -gpu['Price']), reverse=True)
    ram_options.sort(key=lambda ram: (ram['Performance_Score'], -ram['Price']), reverse=True)

    best_package_by_cpu_gpu: dict[tuple[int, int], dict[str, Any]] = {}

    for cpu in cpu_options:
        for gpu in gpu_options:
            for ram in ram_options:
                changed_components: list[dict[str, Any]] = []
                total_upgrade_price = 0.0

                if not cpu.get('_is_current'):
                    changed_components.append(_upgrade_item('CPU', cpu))
                    total_upgrade_price += cpu['Price']

                if not gpu.get('_is_current'):
                    changed_components.append(_upgrade_item('GPU', gpu))
                    total_upgrade_price += gpu['Price']

                if not ram.get('_is_current'):
                    changed_components.append(_upgrade_item('RAM', ram))
                    total_upgrade_price += ram['Price']

                if not changed_components:
                    continue

                if total_upgrade_price > budget:
                    continue

                new_total_power = cpu['Power_Draw'] + gpu['Power_Draw']
                psu_upgrade = None

                if current_psu_wattage < new_total_power:
                    psu_upgrade = _find_required_psu(
                        psu_list,
                        new_total_power,
                        budget - total_upgrade_price,
                    )
                    if psu_upgrade is None:
                        continue
                    total_upgrade_price += psu_upgrade['Price']

                if total_upgrade_price > budget:
                    continue

                new_score = calculate_logic_score(
                    cpu['Performance_Score'],
                    gpu['Performance_Score'],
                    ram['Performance_Score'],
                )

                if new_score <= current_score:
                    continue

                final_cpu_id = cpu['CPU_ID']
                final_gpu_id = gpu['GPU_ID']
                package_key = (final_cpu_id, final_gpu_id)

                upgrade_type = ' + '.join(item['type'] for item in changed_components)
                package = {
                    'type': upgrade_type,
                    'component': changed_components[0]['component'],
                    'components': changed_components,
                    'total_price': round(total_upgrade_price, 2),
                    'previous_score': current_score,
                    'score': new_score,
                    'improvement': round(new_score - current_score, 1),
                    'final_cpu_id': final_cpu_id,
                    'final_gpu_id': final_gpu_id,
                }
                if psu_upgrade is not None:
                    package['psu_upgrade'] = psu_upgrade

                existing_package = best_package_by_cpu_gpu.get(package_key)
                if existing_package is None:
                    best_package_by_cpu_gpu[package_key] = package
                else:
                    new_key = (
                        package['score'],
                        package['improvement'],
                        len(package.get('components', [])),
                        -package['total_price'],
                    )
                    old_key = (
                        existing_package['score'],
                        existing_package['improvement'],
                        len(existing_package.get('components', [])),
                        -existing_package['total_price'],
                    )
                    if new_key > old_key:
                        best_package_by_cpu_gpu[package_key] = package

    upgrade_packages = list(best_package_by_cpu_gpu.values())
    upgrade_packages.sort(
        key=lambda item: (
            item['score'],
            item['improvement'],
            len(item.get('components', [])),
            -item['total_price'],
        ),
        reverse=True,
    )
    return upgrade_packages[:6]
