import sys
from argparse import ArgumentParser
from typing import Optional, Sequence
import logging
from pathlib import Path
import json


import bombcell as bc


def set_up_logging():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def load_phy_params(
    params_py: Path
):
    """Phy params.py is a Python script with parameter assignments.  Evaluate it to get a dictionary of parameters."""
    logging.info(f"Loading params.py: {params_py}")
    params = locals()
    exec(params_py.read_text(), globals(), params)
    for k, v in params.items():
        logging.info(f"  {k}: {v}")
    return params


def capsule_main(
    phy_path: Path,
    phy_pattern: str,
    bombcell_params_json: str,
    results_path: Path
):
    user_bombcell_params = {}
    if bombcell_params_json is not None:
        if bombcell_params_json.endswith(".json"):
            logging.info(f"Loading bombcell params from JSON file: {bombcell_params_json}")
            with open(bombcell_params_json, "r") as f:
                user_bombcell_params = json.load(f)
        else:
            logging.info(f"Loading bombcell params JSON text.")
            user_bombcell_params = json.loads(bombcell_params_json)

    logging.info(f"Searching for params.py(s) within: {phy_path}.")
    logging.info(f"Searching with pattern: {phy_pattern}.")

    params_py_matches = list(phy_path.glob(phy_pattern))
    logging.info(f"Found {len(params_py_matches)} params.py matches: {params_py_matches}")
    if not params_py_matches:
        raise ValueError("Found no matches for params.py.")

    for params_py in params_py_matches:
        phy_params = load_phy_params(params_py)

        # Configure Bombcell parameters.
        # We start with the defaults.
        # We add what we know from the Phy params.py.
        # We add user-supplied values and overrides, if any.
        phy_dir = params_py.parent
        bombcell_params = bc.get_default_parameters(
            phy_dir.as_posix(),
            raw_file=None,
            meta_file=None
        )

        probe_results_path = Path(results_path, phy_dir.name)
        probe_figures_path = Path(probe_results_path, "figures")
        bombcell_params['savePlots'] = True
        bombcell_params['plotsSaveDir'] = probe_figures_path.as_posix()
        bombcell_params['computeDistanceMetrics'] = True
        bombcell_params['ephys_sample_rate'] = phy_params['sample_rate']
        bombcell_params['nChannels'] = phy_params['n_channels_dat']
        bombcell_params['nSyncChannels'] = 0

        if user_bombcell_params:
            logging.info(f"Setting {len(user_bombcell_params)} user-supplied Bombcell params.")
            for name, value in user_bombcell_params.items():
                bombcell_params[name] = value

        logging.info("Using the following Bombcell params:")
        for name, value in bombcell_params.items():
            logging.info(f"  {name}: {value}")

        logging.info("Running Bombcell:")
        bc.run_bombcell(
            phy_dir,
            probe_results_path,
            bombcell_params,
            return_figures=False,
            save_figures=True
        )

        logging.info("OK\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    set_up_logging()

    parser = ArgumentParser(description="Export ecephys sorting resluts to Phy.")

    parser.add_argument(
        "--phy-root", "-P",
        type=str,
        help="Where to search for previously exported Phy data. (default: %(default)s)",
        default="/phy_root"
    )
    parser.add_argument(
        "--phy-pattern", "-p",
        type=str,
        help="Glob pattern used to search within PHY_ROOT for one or more Phy params.py. (default: %(default)s)",
        default="phy/*/params.py"
    )
    parser.add_argument(
        "--bombcell-params-json", "-b",
        type=str,
        help="JSON file name or formatted text with Bombcell parameters. (default: %(default)s)",
        default=None
    )
    parser.add_argument(
        "--results-dir", "-r",
        type=str,
        help="Where to write output result files. (default: %(default)s)",
        default="/results"
    )

    cli_args = parser.parse_args(argv)
    phy_path = Path(cli_args.phy_root)
    results_path = Path(cli_args.results_dir)
    try:
        capsule_main(
            phy_path,
            cli_args.phy_pattern,
            cli_args.bombcell_params_json,
            results_path
        )
    except:
        logging.error("Error running bombcell.", exc_info=True)
        return -1


if __name__ == "__main__":
    exit_code = main(sys.argv[1:])
    sys.exit(exit_code)
