"""Parallel execution helper for adapter calls"""
import concurrent.futures
from typing import Callable, TypeVar

T = TypeVar('T')


def run_parallel(*callables: Callable[[], T], timeout: float = 5.0) -> list[T]:
    """
    Execute multiple callables in parallel using thread pool.

    Args:
        *callables: Functions to execute (no arguments)
        timeout: Maximum time to wait for all results

    Returns:
        List of results in same order as callables

    Raises:
        TimeoutError: If any callable exceeds timeout
        Exception: Re-raises first exception from any callable
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(callables)) as executor:
        futures = [executor.submit(callable_fn) for callable_fn in callables]
        results = []

        for future in concurrent.futures.as_completed(futures, timeout=timeout):
            results.append(future.result())

        # Return results in original order
        return [futures[i].result() for i in range(len(futures))]
