"""Download verified NASA NAIF SPICE kernels for local offline precomputation."""

from pathlib import Path
import ssl
import urllib.request

KERNELS_DIR = Path(__file__).resolve().parents[2] / "kernels"

# Official NASA NAIF generic kernels required for MOON_ME ephemeris calculations
KERNELS = {
    "naif0012.tls": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/lsk/naif0012.tls",
    "de440s.bsp": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440s.bsp",
    "moon_pa_de440_200625.bpc": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/moon_pa_de440_200625.bpc",
    "moon_080317.tf": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/moon_080317.tf",
}


def download_kernels() -> None:
    """Download missing SPICE kernel files into the gitignored kernels directory."""
    KERNELS_DIR.mkdir(parents=True, exist_ok=True)
    ssl_context = ssl._create_unverified_context()

    for filename, url in KERNELS.items():
        destination = KERNELS_DIR / filename
        if destination.exists() and destination.stat().st_size > 0:
            size_mb = destination.stat().st_size / 1e6
            print(f"[OK] Already exists: {filename} ({size_mb:.2f} MB)")
            continue

        print(f"[DOWNLOADING] {filename}...")
        with urllib.request.urlopen(url, context=ssl_context) as response:
            destination.write_bytes(response.read())
        size_mb = destination.stat().st_size / 1e6
        print(f"[DONE] Saved {filename} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    download_kernels()