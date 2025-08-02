#!/usr/bin/env python3
"""
Chunked processing utilities for PiLab Dashboard

This module provides utilities for processing large datasets in chunks.
"""

from typing import List, Any, Callable, Iterator

# Default chunk size
DEFAULT_CHUNK_SIZE = 1000


def process_bulk_data(data: List[Any], 
                     processor: Callable[[List[Any]], Any],
                     chunk_size: int = DEFAULT_CHUNK_SIZE) -> List[Any]:
    """
    Process data in chunks.
    
    Args:
        data: List of data items to process
        processor: Function to process each chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of results from processing
    """
    results = []
    
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        result = processor(chunk)
        results.append(result)
    
    return results


def chunk_data(data: List[Any], chunk_size: int = DEFAULT_CHUNK_SIZE) -> Iterator[List[Any]]:
    """
    Split data into chunks.
    
    Args:
        data: List of data items
        chunk_size: Size of each chunk
        
    Yields:
        Chunks of data
    """
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size] 