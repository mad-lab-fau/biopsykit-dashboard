import nilspodlib
import numpy as np
from nilspodlib.dataset import split_into_sensor_data
from nilspodlib.exceptions import LegacyWarning
from nilspodlib.header import Header
from typing import Dict, Optional, Tuple
import struct
from nilspodlib.legacy import find_conversion_function, legacy_support_check
from nilspodlib.utils import read_binary_uint8, get_strict_version_from_header_bytes
from packaging.version import Version
from typing_extensions import Self
import warnings


def get_header_and_data_bytes(byteFile: bytes) -> Tuple[np.ndarray, np.ndarray]:
    """Separate a binary file into its header and data part."""
    file = bytearray(byteFile)
    header = file[0]
    header_size = header
    header = file[0:header_size]
    data_bytes = file[header_size:]
    data_bytes = np.frombuffer(file, dtype=np.dtype("B"), offset=header_size)
    return np.frombuffer(header, dtype=np.dtype("B")), data_bytes


def parse_binary(
        byteFile: bytes, legacy_support: str = "error", force_version: Optional[Version] = None,
        tz: Optional[str] = None
) -> Tuple[Dict[str, np.ndarray], np.ndarray, Header]:
    header_bytes, data_bytes = get_header_and_data_bytes(byteFile)
    version = get_strict_version_from_header_bytes(header_bytes)
    if legacy_support == "resolve":
        version = force_version or version
        header_bytes, data_bytes = find_conversion_function(version, in_memory=True)(header_bytes, data_bytes)
    elif legacy_support in ["error", "warn"]:
        legacy_support_check(version, as_warning=(legacy_support == "warn"))
    else:
        raise ValueError("legacy_support must be one of 'resolve', 'error' or 'warn'")

    session_header = Header.from_bin_array(header_bytes[1:], tz=tz)

    sample_size = session_header.sample_size
    n_samples = session_header.n_samples

    data = read_binary_uint8(data_bytes, sample_size, n_samples)

    counter, sensor_data = split_into_sensor_data(data, session_header)

    if session_header.strict_version_firmware >= Version("0.13.0") and len(counter) != session_header.n_samples:
        warnings.warn(
            "The number of samples in the dataset does not match the number indicated by the header. "
            "This might indicate a corrupted file",
            LegacyWarning,
        )

    return sensor_data, counter, session_header


class NilsPodAdapted(nilspodlib.Dataset):
    def __init__(self, sensor_data: Dict[str, np.ndarray], counter: np.ndarray, info: Header):
        super().__init__(sensor_data, counter, info)

    @classmethod
    def from_bin_file(
                        cls,
                        byteFile: bytes,
                        *,
                        legacy_support: str = "error",
                        force_version: Optional[Version] = None,
                        tz: Optional[str] = None,
                    ) -> Self:
        sensor_data, counter, info = parse_binary(
            byteFile=byteFile, legacy_support=legacy_support, force_version=force_version, tz=tz
        )
        s = nilspodlib.Dataset(sensor_data, counter, info)
        return s
