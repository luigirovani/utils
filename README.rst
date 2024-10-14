General Utility Module
======================

This project provides general-purpose utility functions commonly used across different Python projects. Currently, it includes utilities for file operations, such as reading, writing, and handling CSV files, as well as secure path joining.

File Operations
---------------

This module provides utility functions for reading, writing, and manipulating file paths. It includes methods for handling plain text files, CSV files, and joining paths while ensuring security.

Features
--------

- **Read Files**: Read the content of a file (text or binary) with options to split lines or ignore errors.
- **Write Files**: Write content (text or binary) to a file.
- **Read CSV Files**: Load CSV data into a list of rows, with options to handle headers and strip whitespace.
- **Write CSV Files**: Write structured data to a CSV file with optional headers.
- **Join Paths**: Safely join multiple paths while ensuring the resulting path stays within a safe directory.

Installation
------------

To use this utility, simply clone the repository and install the necessary dependencies:

.. code-block:: bash

    git clone https://github.com/luigirovani/utils

No external dependencies are required beyond the Python standard library.

Usage
-----

Reading a File
~~~~~~~~~~~~~~

You can read a text file and get its content as a string or split it into lines.

.. code-block:: python

    from utils.files import read

    # Read the entire file as a single string
    content = read('example.txt')
    print(content)

    # Read the file and split it into a list of lines
    lines = read('example.txt', split=True)
    print(lines)

    # Read a binary file
    binary_data = read('example.bin', binary=True)
    print(binary_data)

Writing to a File
~~~~~~~~~~~~~~~~~

Write content to a file as plain text or binary data.

.. code-block:: python

    from utils.files import write

    # Write a string to a file
    write('output.txt', 'This is a test file.')

    # Write binary data to a file
    write('output.bin', b'This is binary data', binary=True)

    # Write a list of lines to a file
    lines = ['First line\n', 'Second line\n', 'Third line\n']
    write('output.txt', lines)

Reading a CSV File
~~~~~~~~~~~~~~~~~~

You can read CSV data into a list of rows, optionally stripping whitespace from each cell.

.. code-block:: python

    from utils.files import read_csv

    # Read the CSV file as a list of rows (list of lists)
    rows = read_csv('data.csv')
    print(rows)

    # Read and drop whitespace from each cell and get unique rows
    cleaned_rows = read_csv('data.csv', drop=True)
    print(cleaned_rows)

Writing to a CSV File
~~~~~~~~~~~~~~~~~~~~~

Write structured data to a CSV file, with optional column headers.

.. code-block:: python

    from utils.files import write_csv

    # Data to write (each inner list represents a row)
    data = [
        ['Name', 'Age', 'City'],
        ['Alice', '30', 'New York'],
        ['Bob', '25', 'Los Angeles']
    ]

    # Write the data to a CSV file with column headers
    write_csv('output.csv', data)

    # Write data without headers
    data_without_header = [
        ['Alice', '30', 'New York'],
        ['Bob', '25', 'Los Angeles']
    ]
    write_csv('output_no_header.csv', data_without_header)

Joining Paths
~~~~~~~~~~~~~

Use the ``join_paths`` function to safely join multiple paths into a single path.

.. code-block:: python

    from utils.files import join_paths

    # Join multiple path segments into a single path
    safe_path = join_paths('/base/dir', 'subdir', 'file.txt')
    print(safe_path)

    # Example that will raise an UnsafePathException if the path is outside the base directory
    try:
        unsafe_path = join_paths('/base/dir', '../../etc/passwd')
    except UnsafePathException as e:
        print(e)

Error Handling
--------------

- **UnsafePathException**: Raised when the ``join_paths`` function tries to resolve a path that is outside the base directory.
- **ignore_errors**: In ``read`` and ``write``, if ``ignore_errors`` is set to ``True``, the function will return an empty result or proceed without raising an exception on errors.

License
-------

This project is licensed under the MIT License.
