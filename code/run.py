import sys
from argparse import ArgumentParser
from typing import Optional, Sequence
import logging
from pathlib import Path


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
    analysis_path: Path,
    phy_pattern: str,
    results_path: Path,
    n_jobs: int,
):
    logging.info(f"Searching for params.py in: {analysis_path}.")
    logging.info(f"Searching with pattern: {phy_pattern}.")

    params_py_matches = list(analysis_path.glob(phy_pattern))
    logging.info(f"Found {len(params_py_matches)} params.py matches: {params_py_matches}")
    params_py = params_py_matches[0]
    phy_params = load_phy_params(params_py)

    # Configure Bombcell parameters.
    # We start with the defaults.
    # We specify what we know from the given params.py and it's surrounding Phy dir.
    # TODO: we also apply user values from a JSON file.
    phy_dir = params_py.parent
    bc_params = bc.get_default_parameters(
        phy_dir.as_posix(),
        raw_file=None,
        meta_file=None
    )

    figures_path = Path(results_path, "figures")
    bc_params['savePlots'] = True
    bc_params['plotsSaveDir'] = figures_path.as_posix()
    bc_params['computeDistanceMetrics'] = True
    bc_params['ephys_sample_rate'] = phy_params['sample_rate']
    bc_params['nChannels'] = phy_params['n_channels_dat']
    bc_params['nSyncChannels'] = 0

    logging.info("Using the following Bombcell params:")
    for k, v in bc_params.items():
        logging.info(f"  {k}: {v}")

    logging.info("Running Bombcell:")
    bc.run_bombcell(
        phy_dir,
        results_path,
        bc_params,
        return_figures=False,
        save_figures=True
    )

    logging.info("OK\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    set_up_logging()

    parser = ArgumentParser(description="Export ecephys sorting resluts to Phy.")

    parser.add_argument(
        "--analysis-dir", "-a",
        type=str,
        help="Where to search for previously exported Phy data. (default: %(default)s)",
        default="/analysis"
    )
    parser.add_argument(
        "--phy-pattern", "-p",
        type=str,
        help="Glob pattern used to search ANALYSIS_DIR for a Phy params.py. (default: %(default)s)",
        default="*/*/exported/phy/*/params.py"
    )
    parser.add_argument(
        "--results-dir", "-r",
        type=str,
        help="Where to write output result files. (default: %(default)s)",
        default="/results"
    )
    parser.add_argument(
        "--n-jobs", "-n",
        type=int,
        help="Number of jobs to use for parallel processing -- -1 means one job per CPU core. (default: %(default)s)",
        default=-1
    )

    cli_args = parser.parse_args(argv)
    analysis_path = Path(cli_args.analysis_dir)
    results_path = Path(cli_args.results_dir)
    try:
        capsule_main(
            analysis_path,
            cli_args.phy_pattern,
            results_path,
            cli_args.n_jobs,
        )
    except:
        logging.error("Error running bombcell.", exc_info=True)
        return -1


if __name__ == "__main__":
    exit_code = main(sys.argv[1:])
    sys.exit(exit_code)
