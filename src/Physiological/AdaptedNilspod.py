from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import nilspodlib
import numpy as np
from nilspodlib import SyncedSession
from nilspodlib.dataset import split_into_sensor_data, Dataset
from nilspodlib.exceptions import LegacyWarning
from nilspodlib.header import Header
from nilspodlib.utils import path_t
from typing import Dict, Optional, Tuple, Iterable
from nilspodlib.legacy import find_conversion_function, legacy_support_check
from nilspodlib.utils import read_binary_uint8, get_strict_version_from_header_bytes
from packaging.version import Version
from typing_extensions import Self
import warnings


def get_header_and_data_bytes(bin_file: BytesIO) -> Tuple[np.ndarray, np.ndarray]:
    """Separate a binary file into its header and data part."""
    header_size = np.frombuffer(bin_file.read(1), dtype=np.dtype("B"))
    header = np.append(
        header_size,
        np.frombuffer(bin_file.read(header_size[0] - 1), dtype=np.dtype("B")),
    )
    data_bytes = np.frombuffer(bin_file.read(), dtype=np.dtype("B"))
    return header, data_bytes


def parse_binary(
    bin_file: BytesIO,
    legacy_support: str = "error",
    force_version: Optional[Version] = None,
    tz: Optional[str] = None,
) -> Tuple[Dict[str, np.ndarray], np.ndarray, Header]:
    header_bytes, data_bytes = get_header_and_data_bytes(bin_file)
    version = get_strict_version_from_header_bytes(header_bytes)
    if legacy_support == "resolve":
        version = force_version or version
        header_bytes, data_bytes = find_conversion_function(version, in_memory=True)(
            header_bytes, data_bytes
        )
    elif legacy_support in ["error", "warn"]:
        legacy_support_check(version, as_warning=(legacy_support == "warn"))
    else:
        raise ValueError("legacy_support must be one of 'resolve', 'error' or 'warn'")

    session_header = Header.from_bin_array(header_bytes[1:], tz=tz)

    sample_size = session_header.sample_size
    n_samples = session_header.n_samples

    data = read_binary_uint8(data_bytes, sample_size, n_samples)

    counter, sensor_data = split_into_sensor_data(data, session_header)

    if (
        session_header.strict_version_firmware >= Version("0.13.0")
        and len(counter) != session_header.n_samples
    ):
        warnings.warn(
            "The number of samples in the dataset does not match the number indicated by the header. "
            "This might indicate a corrupted file",
            LegacyWarning,
        )

    return sensor_data, counter, session_header


class NilsPodAdapted(nilspodlib.Dataset):
    def __init__(
        self, sensor_data: Dict[str, np.ndarray], counter: np.ndarray, info: Header
    ):
        super().__init__(sensor_data, counter, info)

    @classmethod
    def from_bin_file(
        cls,
        filepath_or_buffer: path_t | BytesIO,
        *,
        legacy_support: str = "error",
        force_version: Optional[Version] = None,
        tz: Optional[str] = None,
    ) -> Self:
        if isinstance(filepath_or_buffer, BytesIO):
            sensor_data, counter, info = parse_binary(
                bin_file=filepath_or_buffer,
                legacy_support=legacy_support,
                force_version=force_version,
                tz=tz,
            )
            s = nilspodlib.Dataset(sensor_data, counter, info)
            return s
        else:
            path = Path(filepath_or_buffer)
            if path.suffix != ".bin":
                ValueError(
                    'Invalid file type! Only ".bin" files are supported not {}'.format(
                        path
                    )
                )

            sensor_data, counter, info = parse_binary(
                path, legacy_support=legacy_support, force_version=force_version, tz=tz
            )
            s = nilspodlib.Dataset(sensor_data, counter, info)

            s.path = path
            return s


class SyncedSessionAdapted(nilspodlib.SyncedSession):
    def __init__(self, datasets: Iterable[Dataset]):
        super().__init__(datasets)

    @classmethod
    def from_zip_file(
        cls,
        paths: Iterable[str],
        zip_file: ZipFile,
        legacy_support: str = "error",
        force_version: Version | None = None,
        tz: str | None = None,
    ) -> Self:
        ds = ()
        with zip_file as archive:
            for path in paths:
                ds += NilsPodAdapted.from_bin_file(
                    BytesIO(archive.read(path)),
                    legacy_support=legacy_support,
                    force_version=force_version,
                    tz=tz,
                )
        return SyncedSession(ds)

    @classmethod
    def from_folder_path(
        cls,
        zip_file: ZipFile,
        filter_pattern: str = "*.bin",
        legacy_support: str = "error",
        force_version: Optional[Version] = None,
        tz: Optional[str] = None,
    ) -> Self:
        ds = list(
            filter(lambda file: file.endswith(filter_pattern), zip_file.namelist())
        )  # hier müssen noch alle Dateien gesucht werden
        if not ds:
            raise ValueError(
                'No files matching "{}" where found in zipFile'.format(filter_pattern)
            )
        return SyncedSession(
            cls.from_zip_file(
                paths=ds,
                zip_file=zip_file,
                legacy_support=legacy_support,
                force_version=force_version,
                tz=tz,
            )
        )
