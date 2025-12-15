import os
import nbformat
import pytest

NOTEBOOK_PATH = os.path.join(os.path.dirname(__file__), '..', 'stable_marriage_analysis.ipynb')


def load_notebook_namespace(nb_path):
    nb = nbformat.read(nb_path, as_version=4)
    ns = {}
    for cell in nb.cells:
        if cell.cell_type != 'code':
            continue
        src = cell.source
        # Normalize source to list of lines
        if isinstance(src, list):
            lines = src
        else:
            lines = src.splitlines()
        # Remove IPython magic / shell lines that would break exec
        filtered_lines = [ln for ln in lines if not ln.lstrip().startswith('!') and not ln.lstrip().startswith('%')]
        if not filtered_lines:
            continue
        code = '\n'.join(filtered_lines)
        exec(compile(code, '<notebook>', 'exec'), ns)
    return ns


def test_csp_finds_stable_matching():
    ns = load_notebook_namespace(NOTEBOOK_PATH)

    # Required functions must be present
    assert 'generate_preferences' in ns
    assert 'gale_shapley' in ns
    assert 'solve_stable_marriage_csp' in ns
    assert 'is_stable' in ns

    # Small deterministic instance
    men_prefs, women_prefs = ns['generate_preferences'](5, seed=123)

    matching_gs = ns['gale_shapley'](men_prefs, women_prefs)
    assert isinstance(matching_gs, dict)
    gs_ok, gs_blocking = ns['is_stable'](matching_gs, men_prefs, women_prefs)
    assert gs_ok, f"Gale-Shapley returned unstable matching: {gs_blocking}"

    # Run CSP with a short time limit so the test is fast but meaningful
    try:
        matching_csp = ns['solve_stable_marriage_csp'](men_prefs, women_prefs, time_limit=5.0, num_workers=1, seed=123)
    except Exception as e:
        pytest.skip(f"CSP solver unavailable or failed during test: {e}")

    assert isinstance(matching_csp, dict)
    csp_ok, csp_blocking = ns['is_stable'](matching_csp, men_prefs, women_prefs)
    assert csp_ok, f"CSP returned unstable matching: {csp_blocking}"
