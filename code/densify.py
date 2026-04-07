from pathlib import Path
import logging
from shutil import copy2, move

import numpy as np


def densify_templates(
    phy_dir: Path
):
    """
    SpikeInterface exports cluster waveform templates based on a sparse sampling of spikes.
    Otherwise, the export would take forever and take up a lot of space.

    However, Bombcell expects templates to be represented in a dense way.
    This funciton undoes the sparstity to make Bombcell happy.
    """

    # Confirm we have templates in a sparse form.
    template_ind_npy = Path(phy_dir, "template_ind.npy")
    if not template_ind_npy.exists():
        logging.info(f"Templates appear to be dense already (not sparse), file not found: {template_ind_npy.name}")
        return

    # Move the sparse templates_ind.npy out of the way to not confuse eg. Phy.
    templates_ind_backup_npy = Path(phy_dir, "templates_ind_backup.npy")
    if not templates_ind_backup_npy.exists():
        logging.info(f"Moving the original {template_ind_npy.name} to {templates_ind_backup_npy}")
        move(template_ind_npy, templates_ind_backup_npy)

    # Save a copy of the sparse templates.npy from eg Spike Interface.
    templates_npy = Path(phy_dir, "templates.npy")
    templates_backup_npy = Path(phy_dir, "templates_backup.npy")
    if not templates_backup_npy.exists():
        logging.info(f"Save a backup of the original {templates_npy.name}: {templates_backup_npy}")
        copy2(templates_npy, templates_backup_npy)

    # Sparse templates.npy has shape (num_units, num_samples, max_num_channels).
    # The max_num_channels dimension is sparse, with raw channel indices stored separately in template_ind.npy.
    templates = np.load(templates_backup_npy)
    template_ind = np.load(templates_ind_backup_npy)

    # Reconstruct a full matrix with shape (num_units, num_samples, num_channels).
    num_units = templates.shape[0]
    num_samples = templates.shape[1]
    num_channels = template_ind.max() + 1
    full_templates = np.zeros((num_units, num_samples, num_channels), dtype=templates.dtype)
    for unit_index in range(num_units):
        channel_indices = template_ind[unit_index]
        channel_is_present = np.nonzero(channel_indices >= 0)[0]
        unit_template = templates[unit_index, :, channel_is_present]
        full_templates[unit_index, :, channel_indices[channel_is_present]] = unit_template

    # Replace the original templates.npy with the densified version.
    logging.info(f"Computed dense templates with shape {full_templates.shape}")
    logging.info(f"Saving dense templates: {templates_npy}")
    templates_npy.unlink()
    np.save(templates_npy, full_templates)
