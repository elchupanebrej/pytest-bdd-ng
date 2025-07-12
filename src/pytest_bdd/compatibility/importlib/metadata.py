import sys

if sys.version_info >= (3, 10):
    from importlib.metadata import (
        Distribution,
        DistributionFinder,
        PackageMetadata,
        PackageNotFoundError,
        distribution,
        distributions,
        entry_points,
        files,
        metadata,
        packages_distributions,
        requires,
        version,
    )

else:
    from importlib_metadata import (
        Distribution,
        DistributionFinder,
        PackageMetadata,
        PackageNotFoundError,
        distribution,
        distributions,
        entry_points,
        files,
        metadata,
        packages_distributions,
        requires,
        version,
    )


__all__ = [
    "Distribution",
    "DistributionFinder",
    "PackageMetadata",
    "PackageNotFoundError",
    "distribution",
    "distributions",
    "entry_points",
    "files",
    "metadata",
    "packages_distributions",
    "requires",
    "version",
]
