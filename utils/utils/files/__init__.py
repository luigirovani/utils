from typing import Union, List, Optional, Tuple
from collections.abc import Iterable
from pathlib import Path
import csv

__all__ = ['read', 'write', 'read_csv', 'write_csv', 'join_paths']


class UnsafePathException(Exception):
    """Exception raised for unsafe paths."""
    pass
 
def read(
    path: Union[str, Path],
    encoding: str = 'utf-8',
    split: bool = False,
    drop_empty: bool = True,
    ignore_errors: bool = False,
    binary: bool = False,
    **kwargs
) -> Union[str, bytes, List[str]]:
    """
    Reads content from a file.

    Args:
        path (Union[str, Path]): The file path to read from.
        encoding (str, optional): Encoding to use for reading text files. Defaults to 'utf-8'.
        split (bool, optional): If True, splits the file content into a list of lines. Defaults to False.
        ignore_errors (bool, optional): If True, returns an empty string or list when an error occurs. Defaults to True.
        binary (bool, optional): If True, reads the file in binary mode. Defaults to False.
        **kwargs: Additional arguments passed to the `open` function.

    Returns:
        Union[str, bytes, List[str]]: The file content as a string, bytes, or list of lines depending on the parameters.

    Raises:
        Exception: Raises an exception if `ignore_errors` is set to False and an error occurs.
    """
    try:

        if binary:
            return _read_bin(path, **kwargs)

        text = _read_text(path, encoding, **kwargs)

        if not split:
            return text

        if drop_empty:
            return [line.strip() for line in text.splitlines() if line.strip()]
        
        return text.splitlines()

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
    """
    Writes content to a file.

    Args:
        path (Union[str, Path]): The file path to write to.
        content (Union[str, bytes, Iterable[str]]): The content to write to the file (text or binary).
        encoding (str, optional): Encoding to use for writing text files. Defaults to 'utf-8'.
        ignore_errors (bool, optional): If True, ignores errors during writing. Defaults to False.
        binary (bool, optional): If True, writes the file in binary mode. Defaults to False.
        **kwargs: Additional arguments passed to the `open` function.

    Returns:
        None

    Raises:
        Exception: Raises an exception if `ignore_errors` is set to False and an error occurs.
    """
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
    skip_header: bool = False,
    **kwargs
) -> List[Optional[Union[List[str], Tuple[str]]]]:
    """
    Reads a CSV file and returns the rows.

    Args:
        path (Union[str, Path]): The file path to the CSV file.
        delimiter (str, optional): The character used to separate fields. Defaults to ','.
        encoding (str, optional): Encoding to use for reading the CSV file. Defaults to 'utf-8'.
        ignore_errors (bool, optional): If True, ignores errors during reading. Defaults to False.
        newline (str, optional): Specifies how newline characters should be handled. Defaults to ''.
        drop (bool, optional): If True, strips whitespace from each field. Defaults to False.
        skip_header (bool, optional): If True, skips the header row of the CSV file. Defaults to False.
        **kwargs: Additional arguments passed to the `csv.reader` function.

    Returns:
        List[Optional[Union[List[str], Tuple[str]]]]: A list of rows, where each row is a list or tuple of strings.

    Raises:
        Exception: Raises an exception if `ignore_errors` is set to False and an error occurs.
    """
    try:
        rows = _read_csv(path, newline, encoding, delimiter, **kwargs)

        if skip_header:
            next(rows)

        if drop:
            rows = set(tuple(map(lambda c: c.strip(), row)) for row in rows)

        return list(rows)

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
    """
    Writes data to a CSV file.

    Args:
        path (Union[str, Path]): The file path to write to.
        data (Iterable[Iterable[str]]): Data to write, where each item is a row of strings.
        delimiter (str, optional): The character used to separate fields. Defaults to ','.
        encoding (str, optional): Encoding to use for writing the CSV file. Defaults to 'utf-8'.
        newline (str, optional): Specifies how newline characters should be handled. Defaults to ''.
        header (Optional[Iterable[str]], optional): A list of column headers to write before the data. Defaults to None.
        **kwargs: Additional arguments passed to the `csv.writer` function.

    Returns:
        None
    """
    with open(path, mode='w', encoding=encoding, newline=newline, **kwargs) as f:
        writer = csv.writer(f, delimiter=delimiter)
        if header:
            writer.writerow(header)
        writer.writerows(data)


def join_paths(
    *paths: Union[str, Path], 
    check: bool = False, 
    mkdir: bool = False,
    eafp: bool = False
) -> Path:
    """
    Joins multiple paths into a single absolute path 

    Args:
        *paths (Union[str, Path]): One or more paths to join together. The first path 
            is considered the "base directory," and the resulting path must remain within 
            this directory for security reasons.
        check (bool, optional): If `True`, the function checks if the resolved path exists, 
            raising a `FileNotFoundError` if it does not. Defaults to `False`.
        mkdir (bool, optional): If `True`, the function creates the parent directories 
            of the resolved path if they do not exist, using `Path.mkdir()`.
        EAFP (bool, optional): easier to ask forgiveness than permission

    Returns:
        Path: The fully joined and resolved path as a `Path` object.

    Raises:
        ValueError: If no paths are provided.
        UnsafePathException: If the resulting path is outside the base directory.
        FileNotFoundError: If `check` is `True` and the path does not exist.

    Note:
        This function ensures that the final path is within the base directory for security 
        reasons. This can help prevent issues like directory traversal attacks when handling 
        file paths dynamically.
    """

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

    if check and not resolved_path.exists():
        raise FileNotFoundError(f"The path {resolved_path} does not exist")

    elif mkdir and (not eafp or resolved_path.parent.exists()):
        resolved_path.parent.mkdir(parents=True, exist_ok=True)

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

def _read_text(path, encoding, **kwargs) -> Union[str, List[str]]:
    with open(path, encoding=encoding, **kwargs) as f:
        return f.read()

def _read_csv(path, newline, encoding, delimiter, **kwargs) -> Iterable[str]:
    with open(path, mode='r', newline=newline, encoding=encoding, **kwargs) as f:
        return csv.reader(f, delimiter=delimiter)