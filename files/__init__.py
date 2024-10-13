from typing import Union, List, Optional, Tuple
from collections.abc import Iterable
from pathlib import Path
import csv
import os 

__all__ = ['read', 'write', 'read_csv', 'write_csv', 'join_paths']
'easier to ask forgiveness than permission (EAFP)'


class UnsafePathException(Exception):
    """Exception raised for unsafe paths."""
    pass

def read(
    path: Union[str, Path],
    encoding: str = 'utf-8',
    split: bool = False,
    ignore_errors: bool = True,
    binary: bool = False,
    **kwargs
) -> Union[str, bytes, List[str]]:
    
    try:
        if binary:
            return _read_bin(path, **kwargs)
        return _read_text(path, encoding=encoding, **kwargs)

    except Exception as e:
        if ignore_errors and not binary:
            return '' if split else []
        raise e

def write(
    path: Union[str, Path],
    content: Union[str, bytes, Iterable[str]],
    encoding: str = 'utf-8',
    ignore_errors: bool = False,
    binary: bool = False,
    **kwargs
) -> None:

    try:
        if binary:
            return _write_bin(path, content, **kwargs)
        return _write_text(path, encoding, content, **kwargs)
    except Exception as e:
        if not ignore_errors:
            raise e


def read_csv(
    path: Union[str, Path],
    delimiter: str = ',',
    encoding: str = 'utf-8',
    ignore_errors: bool = False,
    newline: str ='',
    drop: bool = False,
    **kwargs
) -> List[Optional[Union[List[str],Tuple[str]]]]:

    try:
        rows = _read_csv(path, newline, encoding, delimiter, **kwargs)
        if drop:
            return [tuple(map(lambda c: c.strip()), row) for row in rows]
        return rows
    except Exception as e:
        if not ignore_errors:
            raise e
        return []

def write_csv(
    path: Union[str, Path],
    data: Iterable[Iterable[str]],
    delimiter: str = ',',
    encoding: str = 'utf-8',
    newline: str ='',
    header: Optional[Iterable[str]] = None,
    **kwargs
) -> None:

    with open(path, mode='w', encoding=encoding, newline=newline, **kwargs) as f:
        writer = csv.writer(f, delimiter=delimiter)
        if header:
            writer.writerow(header)
        writer.writerows(data)


def join_paths(*paths: Union[str, Path]) -> Path:
    if len(paths) < 1:
        raise ValueError("At least one path must be provided.")

    paths = [Path(p) if isinstance(p, str) else p for p in paths]
    base_dir = paths[0].resolve()

    full_path = base_dir
    for p in paths[1:]:
        full_path = full_path / p

    resolved_path = full_path.resolve()

    if not resolved_path.is_relative_to(base_dir):
        raise UnsafePathException(f"The path {resolved_path} is outside the safe directory {base_dir}.")

    return resolved_path


def _read_bin(path, **kwargs) -> bytes:
    with open(path, mode='rb', **kwargs) as f:
        return f.read()

def _write_bin(path, content: bytes, **kwargs) -> None:
    with open(path, mode='wb', **kwargs) as f:
        return f.write(content)
 
def _write_text(path, encoding, content: str, **kwargs) -> None:
    with open(path, 'w', encoding=encoding, **kwargs) as f:
        if isinstance(content, Iterable):
            f.writelines(content)
        else:
            f.write(content)

def _read_text(path, encoding, split, **kwargs) -> Union[str, List[str]]:
    with open(path, encoding=encoding, **kwargs) as f:
        text = f.read()
        if split:
            return list(text.splitlines())
        return text

def _read_csv(path, newline, encoding, delimiter, **kwargs) -> List[str]:
    with open(path, mode='r', newline=newline, encoding=encoding, **kwargs) as f:
        return list(csv.reader(f, delimiter=delimiter))