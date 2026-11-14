"""LUNARIS M2 Direct-to-Earth (DTE) Communication Visibility & RF Link Budget Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
import numpy as np

from .illumination import HorizonProfile, interpolate_horizon_el

# Speed of light [m/s] and Boltzmann constant [J/K]
SPEED_OF_LIGHT_M_S = 299_792_458.0
BOLTZMANN_DBW_K_HZ = -228.6
MEAN_EARTH_MOON_DISTANCE_KM = 384_400.0


class LinkError(Exception):
    """Domain error for invalid RF link parameters, elevation limits, or input lengths."""


@dataclass(frozen=True)
class RFLinkConfig:
    """Direct-to-Earth (DTE) X-band / S-band lunar lander telecommunications profile.

    Defaults represent an X-band (~8.4 GHz) lunar lander communicating with a 34 m DSN station.
    """

    frequency_ghz: float = 8.4
    tx_power_w: float = 15.0
    tx_antenna_gain_dbi: float = 18.0
    rx_antenna_gain_dbi: float = 68.0
    system_noise_temp_k: float = 75.0
    line_and_pointing_loss_db: float = 2.5
    required_eb_n0_db: float = 4.5
    min_elevation_margin_deg: float = 1.0
    target_data_rate_kbps: float = 256.0
    antenna_boresight_az_deg: float | None = None
    antenna_boresight_el_deg: float | None = None

    def __post_init__(self) -> None:
        if self.frequency_ghz <= 0.0:
            raise LinkError("frequency_ghz must be strictly positive.")
        if self.tx_power_w <= 0.0:
            raise LinkError("tx_power_w must be strictly positive.")
        if self.system_noise_temp_k <= 0.0:
            raise LinkError("system_noise_temp_k must be strictly positive.")
        if self.target_data_rate_kbps <= 0.0:
            raise LinkError("target_data_rate_kbps must be strictly positive.")
        if (self.antenna_boresight_az_deg is None) != (
            self.antenna_boresight_el_deg is None
        ):
            raise LinkError("Both antenna boresight azimuth and elevation must be supplied.")
        if self.antenna_boresight_az_deg is not None and not (
            0.0 <= self.antenna_boresight_az_deg < 360.0
        ):
            raise LinkError("antenna_boresight_az_deg must be within [0, 360).")
        if self.antenna_boresight_el_deg is not None and not (
            -90.0 <= self.antenna_boresight_el_deg <= 90.0
        ):
            raise LinkError("antenna_boresight_el_deg must be within [-90, 90].")


def free_space_path_loss_db(distance_km: float, frequency_ghz: float) -> float:
    """Compute Free-Space Path Loss (FSPL) [dB] for slant range [km] and carrier [GHz]."""
    if distance_km <= 0.0 or frequency_ghz <= 0.0:
        raise LinkError("distance_km and frequency_ghz must be strictly positive.")
    dist_m = float(distance_km) * 1000.0
    freq_hz = float(frequency_ghz) * 1e9
    fspl = 20.0 * np.log10(dist_m) + 20.0 * np.log10(freq_hz) + 20.0 * np.log10(
        4.0 * np.pi / SPEED_OF_LIGHT_M_S
    )
    return float(fspl)


def evaluate_dte_link(
    earth_az_deg: float,
    earth_el_deg: float,
    horizon_profile: HorizonProfile | None = None,
    distance_km: float = MEAN_EARTH_MOON_DISTANCE_KM,
    config: RFLinkConfig | None = None,
) -> dict:
    """Evaluate DTE visibility, optional boresight error, and RF link margin."""
    cfg = config or RFLinkConfig()
    geometric_los = bool(earth_el_deg > 0.0)
    pointing_error_deg = None
    if (
        cfg.antenna_boresight_az_deg is not None
        and cfg.antenna_boresight_el_deg is not None
    ):
        target_az_rad, target_el_rad = np.radians([earth_az_deg, earth_el_deg])
        boresight_az_rad, boresight_el_rad = np.radians(
            [cfg.antenna_boresight_az_deg, cfg.antenna_boresight_el_deg]
        )
        target_direction = np.array(
            [
                np.cos(target_el_rad) * np.sin(target_az_rad),
                np.cos(target_el_rad) * np.cos(target_az_rad),
                np.sin(target_el_rad),
            ]
        )
        boresight_direction = np.array(
            [
                np.cos(boresight_el_rad) * np.sin(boresight_az_rad),
                np.cos(boresight_el_rad) * np.cos(boresight_az_rad),
                np.sin(boresight_el_rad),
            ]
        )
        pointing_error_deg = float(
            np.degrees(
                np.arccos(np.clip(np.dot(target_direction, boresight_direction), -1.0, 1.0))
            )
        )

    if horizon_profile is None:
        horizon_el = None
        terrain_clearance_deg = None
        terrain_los = None
        terrain_available = False
    else:
        horizon_el = interpolate_horizon_el(earth_az_deg, horizon_profile)
        terrain_clearance_deg = float(earth_el_deg) - horizon_el
        terrain_los = bool(terrain_clearance_deg >= cfg.min_elevation_margin_deg)
        terrain_available = True

    fspl_db = free_space_path_loss_db(distance_km=distance_km, frequency_ghz=cfg.frequency_ghz)
    tx_power_dbw = 10.0 * np.log10(cfg.tx_power_w)
    eirp_dbw = tx_power_dbw + cfg.tx_antenna_gain_dbi

    # Received isotropic power and C/N0 [dB-Hz]
    rx_power_dbw = eirp_dbw - fspl_db - cfg.line_and_pointing_loss_db + cfg.rx_antenna_gain_dbi
    n0_dbw_hz = BOLTZMANN_DBW_K_HZ + 10.0 * np.log10(cfg.system_noise_temp_k)
    c_n0_db_hz = rx_power_dbw - n0_dbw_hz

    # Achievable Eb/N0 at target data rate and maximum supported data rate with required Eb/N0
    data_rate_db_hz = 10.0 * np.log10(cfg.target_data_rate_kbps * 1000.0)
    eb_n0_db = c_n0_db_hz - data_rate_db_hz
    link_margin_db = eb_n0_db - cfg.required_eb_n0_db

    max_rate_db_hz = c_n0_db_hz - cfg.required_eb_n0_db
    visibility = terrain_los if terrain_available else geometric_los
    max_data_rate_kbps = (
        float((10.0 ** (max_rate_db_hz / 10.0)) / 1000.0) if visibility else 0.0
    )

    link_active = bool(visibility and link_margin_db >= 0.0)

    return {
        "geometric_los": geometric_los,
        "terrain_los": terrain_los,
        "link_active": link_active,
        "earth_az_deg": round(float(earth_az_deg) % 360.0, 4),
        "earth_el_deg": round(float(earth_el_deg), 4),
        "pointing_error_deg": (
            None if pointing_error_deg is None else round(pointing_error_deg, 4)
        ),
        "horizon_el_deg": None if horizon_el is None else round(horizon_el, 4),
        "clearance_deg": (
            None if terrain_clearance_deg is None else round(terrain_clearance_deg, 4)
        ),
        "distance_km": round(float(distance_km), 2),
        "fspl_db": round(fspl_db, 2),
        "c_n0_db_hz": round(c_n0_db_hz, 2),
        "eb_n0_db": round(eb_n0_db, 2),
        "link_margin_db": round(link_margin_db, 2),
        "achievable_data_rate_kbps": round(max_data_rate_kbps, 2),
        "geometric_provenance": "CALCULATED",
        "provenance": "ESTIMATED",
        "terrain_available": terrain_available,
    }


def summarize_comm_windows(
    times_utc: Sequence[str],
    earth_az_deg: Sequence[float],
    earth_el_deg: Sequence[float],
    horizon_profile: HorizonProfile | None = None,
    distances_km: Sequence[float] | None = None,
    config: RFLinkConfig | None = None,
) -> dict:
    """Compute time-series DTE communication visibility, AOS/LOS transitions, and link budget."""
    n = len(times_utc)
    if n == 0 or len(earth_az_deg) != n or len(earth_el_deg) != n:
        raise LinkError("times_utc, earth_az_deg, and earth_el_deg must have matching non-zero length.")

    if distances_km is not None:
        if len(distances_km) != n:
            raise LinkError("distances_km must match times_utc length.")
        dists = [float(d) for d in distances_km]
    else:
        dists = [MEAN_EARTH_MOON_DISTANCE_KM] * n

    series = []
    events = []
    prev_active: bool | None = None

    for t_str, az, el, dist in zip(times_utc, earth_az_deg, earth_el_deg, dists):
        step = evaluate_dte_link(
            earth_az_deg=float(az),
            earth_el_deg=float(el),
            horizon_profile=horizon_profile,
            distance_km=dist,
            config=cfg if (cfg := config) else None,
        )
        step["time_utc"] = str(t_str)
        series.append(step)

        curr_active = step["link_active"]
        if prev_active is not None and curr_active != prev_active:
            events.append(
                {
                    "time_utc": str(t_str),
                    "event": "AOS" if curr_active else "LOS",
                    "earth_az_deg": step["earth_az_deg"],
                    "earth_el_deg": step["earth_el_deg"],
                    "horizon_el_deg": step["horizon_el_deg"],
                    "link_margin_db": step["link_margin_db"],
                }
            )
        prev_active = curr_active

    active_steps = [r for r in series if r["link_active"]]
    comm_availability = len(active_steps) / n
    mean_rate_kbps = (
        sum(r["achievable_data_rate_kbps"] for r in active_steps) / len(active_steps)
        if active_steps
        else 0.0
    )

    return {
        "sample_count": n,
        "comm_availability_fraction": round(comm_availability, 4),
        "mean_active_data_rate_kbps": round(mean_rate_kbps, 2),
        "events": events,
        "series": series,
        "geometric_provenance": "CALCULATED",
        "provenance": "ESTIMATED",
        "terrain_available": horizon_profile is not None,
    }