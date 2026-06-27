from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

from flask import Flask, redirect, render_template, request, session, url_for

from backend.comparison import compare_builds
from backend.db import fetch_all, init_database
from backend.optimisation import optimise_build, recommend_upgrade

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.secret_key = 'buildlogicpcs-secret-key'

init_database(force_reset=False)


def _get_table_data() -> dict[str, list[dict]]:
    return {
        'cpus': fetch_all('CPU'),
        'gpus': fetch_all('GPU'),
        'motherboards': fetch_all('MOTHERBOARD'),
        'ram_modules': fetch_all('RAM'),
        'psus': fetch_all('PSU'),
        'cases': fetch_all('CASE'),
        'games': fetch_all('GAMES'),
        'game_presets': fetch_all('GAMES_PRESET_APPLIED'),
    }


def _component_title(component_type: str, component: dict) -> str:
    brand = str(component.get('Brand', '')).strip()
    model = str(component.get('Model', '')).strip()
    if brand and brand.lower() not in model.lower():
        return f'{brand} {model}'.strip()
    return model or brand or component_type


def _purchase_link(component_type: str, component: dict) -> str:
    query = f"{_component_title(component_type, component)} {component_type} buy UK"
    return f"https://www.google.com/search?tbm=shop&q={quote_plus(query)}"


def _make_purchase_item(component_type: str, component: dict) -> dict:
    return {
        'type': component_type,
        'name': _component_title(component_type, component),
        'price': component.get('Price', 0),
        'purchase_link': _purchase_link(component_type, component),
    }


def _store_purchase_summary(title: str, components: list[dict], total_price: float, note: str = '') -> None:
    session['purchase_summary'] = {
        'title': title,
        'components': components,
        'total_price': round(total_price, 2),
        'note': note,
    }


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/new-build', methods=['GET', 'POST'])
def new_build():
    data = _get_table_data()
    if request.method == 'POST':
        budget = float(request.form['budget'])
        game_id = int(request.form['game_id'])
        preset = request.form['preset'].upper()

        builds = optimise_build(
            data['cpus'],
            data['gpus'],
            data['motherboards'],
            data['ram_modules'],
            data['psus'],
            data['game_presets'],
            budget,
            game_id,
            preset,
        )

        session['new_build_results'] = builds
        return redirect(url_for('build_results'))

    return render_template('new_build.html', games=data['games'])


@app.route('/build-results')
def build_results():
    builds = session.get('new_build_results', [])
    return render_template('results.html', builds=builds, result_type='build')


@app.route('/case-design', methods=['GET', 'POST'])
def case_design():
    data = _get_table_data()
    selected_build = session.get('selected_build_for_case')
    chosen_case = None
    final_total_price = None

    if request.method == 'POST':
        if 'selected_builds' in request.form:
            selected_indices = request.form.getlist('selected_builds')
            builds = session.get('new_build_results', [])

            if len(selected_indices) != 1:
                return redirect(url_for('build_results'))

            selected_build = builds[int(selected_indices[0])]
            session['selected_build_for_case'] = selected_build

            return render_template(
                'case_design.html',
                build=selected_build,
                cases=data['cases'],
                chosen_case=None,
                final_total_price=None,
            )

        if 'case_id' in request.form:
            if not selected_build:
                return redirect(url_for('build_results'))

            case_id = int(request.form['case_id'])
            chosen_case = next(case for case in data['cases'] if case['Case_ID'] == case_id)
            final_total_price = round(selected_build['total_price'] + chosen_case['Price'], 2)

            final_build = dict(selected_build)
            final_build['case'] = chosen_case
            final_build['total_price'] = final_total_price
            session['final_build_with_case'] = final_build

            components = [
                _make_purchase_item('CPU', final_build['cpu']),
                _make_purchase_item('GPU', final_build['gpu']),
                _make_purchase_item('Motherboard', final_build['motherboard']),
                _make_purchase_item('RAM', final_build['ram']),
                _make_purchase_item('PSU', final_build['psu']),
                _make_purchase_item('Case', final_build['case']),
            ]
            _store_purchase_summary(
                'Final Build Purchase Links',
                components,
                final_total_price,
                'These are static purchase search links for each selected component.',
            )
            return redirect(url_for('purchase_summary'))

    if not selected_build:
        return redirect(url_for('build_results'))

    return render_template(
        'case_design.html',
        build=selected_build,
        cases=data['cases'],
        chosen_case=chosen_case,
        final_total_price=final_total_price,
    )


@app.route('/upgrade', methods=['GET', 'POST'])
def upgrade():
    data = _get_table_data()
    if request.method == 'POST':
        budget = float(request.form['budget'])
        cpu_id = int(request.form['cpu_id'])
        gpu_id = int(request.form['gpu_id'])
        ram_id = int(request.form['ram_id'])
        psu_id = int(request.form['psu_id'])

        selected_cpu = next(cpu for cpu in data['cpus'] if cpu['CPU_ID'] == cpu_id)
        selected_gpu = next(gpu for gpu in data['gpus'] if gpu['GPU_ID'] == gpu_id)
        selected_ram = next(ram for ram in data['ram_modules'] if ram['RAM_ID'] == ram_id)
        selected_psu = next(psu for psu in data['psus'] if psu['PSU_ID'] == psu_id)

        existing_build = {
            'CPU_ID': selected_cpu['CPU_ID'],
            'GPU_ID': selected_gpu['GPU_ID'],
            'RAM_ID': selected_ram['RAM_ID'],
            'PSU_ID': selected_psu['PSU_ID'],
            'CPU_Model': selected_cpu['Model'],
            'GPU_Model': selected_gpu['Model'],
            'RAM_Model': selected_ram['Model'],
            'PSU_Model': selected_psu['Model'],
            'CPU_Score': selected_cpu['Performance_Score'],
            'GPU_Score': selected_gpu['Performance_Score'],
            'RAM_Score': selected_ram['Performance_Score'],
            'CPU_Power_Draw': selected_cpu['Power_Draw'],
            'GPU_Power_Draw': selected_gpu['Power_Draw'],
            'PSU_Wattage': selected_psu['Wattage'],
            'Socket_Type': selected_cpu['Socket_Type'],
            'RAM_Type': selected_ram['RAM_Type'],
        }

        upgrades = recommend_upgrade(
            existing_build,
            budget,
            data['cpus'],
            data['gpus'],
            data['ram_modules'],
            data['psus'],
        )

        session['upgrade_results'] = upgrades
        return redirect(url_for('upgrade_results'))

    return render_template(
        'upgrade.html',
        games=data['games'],
        cpus=data['cpus'],
        gpus=data['gpus'],
        ram_modules=data['ram_modules'],
        psus=data['psus'],
    )


@app.route('/upgrade-results')
def upgrade_results():
    upgrades = session.get('upgrade_results', [])
    return render_template('results.html', builds=upgrades, result_type='upgrade')


@app.route('/upgrade-purchase', methods=['POST'])
def upgrade_purchase():
    selected_index = int(request.form['upgrade_index'])
    upgrades = session.get('upgrade_results', [])

    if selected_index < 0 or selected_index >= len(upgrades):
        return redirect(url_for('upgrade_results'))

    upgrade_package = upgrades[selected_index]
    components = []

    for item in upgrade_package.get('components', []):
        components.append(_make_purchase_item(item['type'], item['component']))

    if upgrade_package.get('psu_upgrade'):
        components.append(_make_purchase_item('PSU', upgrade_package['psu_upgrade']))

    if not components and upgrade_package.get('component'):
        components.append(_make_purchase_item(upgrade_package.get('type', 'Component'), upgrade_package['component']))

    _store_purchase_summary(
        'Upgrade Purchase Links',
        components,
        upgrade_package.get('total_price', 0),
        'These links are for the recommended upgrade components only.',
    )
    return redirect(url_for('purchase_summary'))


@app.route('/purchase-summary')
def purchase_summary():
    summary = session.get('purchase_summary')
    if not summary:
        return redirect(url_for('home'))
    return render_template('purchase_summary.html', summary=summary)


@app.route('/compare', methods=['POST'])
def compare():
    selected_indices = request.form.getlist('selected_builds')
    builds = session.get('new_build_results', [])

    if len(selected_indices) != 2:
        return redirect(url_for('build_results'))

    build1 = builds[int(selected_indices[0])]
    build2 = builds[int(selected_indices[1])]
    comparison = compare_builds(build1, build2)
    return render_template('compare.html', comparison=comparison)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
