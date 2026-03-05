"""
core/parallel_utils.py - Thread-pool helpers for bulk asset processing

Provides a thin wrapper around concurrent.futures.ThreadPoolExecutor
so that all commands use consistent parallelism settings and error handling.

Public API
----------
parallel_map(fn, items, workers=4, ordered=True)  -> list
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")

# Default worker count: use half the available CPUs, min 2, max 16
_DEFAULT_WORKERS = max(2, min(16, (os.cpu_count() or 4) // 2))


def parallel_map(
    fn: Callable[[T], R],
    items: Iterable[T],
    workers: int = _DEFAULT_WORKERS,
    ordered: bool = True,
) -> list[R]:
    """
    Apply *fn* to every element of *items* using a thread pool.

    Parameters
    ----------
    fn      : callable that takes a single item and returns a result
    items   : iterable of inputs
    workers : number of concurrent threads (default: half CPU count, min 2)
    ordered : if True (default), results preserve input order;
              if False, results arrive in completion order (faster for I/O)

    Returns
    -------
    list of results in input order (ordered=True) or completion order (False)

    Notes
    -----
    Exceptions raised inside *fn* are re-raised by parallel_map after all
    futures have been submitted, so all items are attempted before failing.
    If multiple items raise, only the first exception is propagated.
    """
    item_list = list(items)
    if not item_list:
        return []

    if workers == 1:
        # Single-threaded fast-path (easier to debug)
        return [fn(item) for item in item_list]

    results   = [None] * len(item_list)
    first_exc = None

    with ThreadPoolExecutor(max_workers=workers) as pool:
        if ordered:
            # Submit all, collect in order
            futures = [pool.submit(fn, item) for item in item_list]
            for i, fut in enumerate(futures):
                try:
                    results[i] = fut.result()
                except Exception as exc:
                    if first_exc is None:
                        first_exc = exc
                    results[i] = None
        else:
            # Submit with index tag, collect as completed
            future_to_idx = {pool.submit(fn, item): i for i, item in enumerate(item_list)}
            for fut in as_completed(future_to_idx):
                i = future_to_idx[fut]
                try:
                    results[i] = fut.result()
                except Exception as exc:
                    if first_exc is None:
                        first_exc = exc
                    results[i] = None

    if first_exc is not None:
        raise first_exc

    return results


def parallel_map_safe(
    fn: Callable[[T], R],
    items: Iterable[T],
    workers: int = _DEFAULT_WORKERS,
    default = None,
) -> list[R]:
    """
    Like parallel_map but NEVER raises.  Failed items return *default*.
    Useful for bulk scans where individual failures are acceptable.
    """
    item_list = list(items)
    if not item_list:
        return []

    if workers == 1:
        out = []
        for item in item_list:
            try:
                out.append(fn(item))
            except Exception:
                out.append(default)
        return out

    results = [default] * len(item_list)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_to_idx = {pool.submit(fn, item): i for i, item in enumerate(item_list)}
        for fut in as_completed(future_to_idx):
            i = future_to_idx[fut]
            try:
                results[i] = fut.result()
            except Exception:
                results[i] = default

    return results
