# toolkit/parallel.py
# Parallel asset scanning using concurrent.futures ThreadPoolExecutor.

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Tuple, Optional, Any


def parallel_map(
    fn: Callable[[int], Any],
    ids: List[int],
    workers: int = 4,
    progress_cb: Optional[Callable[[int, int], None]] = None,
) -> List[Tuple[int, Any]]:
    """
    Maps fn(asset_id) over all ids in parallel.
    Returns list of (asset_id, result) tuples in completion order.
    """
    results = []
    total = len(ids)
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_id = {executor.submit(fn, asset_id): asset_id for asset_id in ids}
        for future in as_completed(future_to_id):
            asset_id = future_to_id[future]
            try:
                result = future.result()
            except Exception:
                result = None
            results.append((asset_id, result))
            completed += 1
            if progress_cb:
                progress_cb(completed, total)

    # Sort results by asset_id for deterministic ordering
    results.sort(key=lambda x: x[0])
    return results
