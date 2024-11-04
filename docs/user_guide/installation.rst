How to install ``tqec``
=======================

Requirements before installing
------------------------------

Python version
~~~~~~~~~~~~~~

The ``tqec`` package only supports Python 3.10 and onward. If you have Python 3.9 or below,
please update your Python installation.

Additional toolchains
~~~~~~~~~~~~~~~~~~~~~

Some of the dependencies of ``tqec`` are implemented using compiled languages. This is for
example the case of the `pycryptosat <https://pypi.org/project/pycryptosat/>`_ dependency.
Pre-compiled Python packages that should be compatible with any GNU/Linux are provided
by the author, but no pre-compiled package exist for Windows or MacOS.

This means that, if you try to install the ``tqec`` package on Windows or MacOS, a working
C++ toolchain should also be installed on your system.

Here is a list of potential issues you might encounter and how to solve them:

- `Failed building wheel for pycryptosat <https://github.com/QCHackers/tqec/issues/311>`_

Installation procedure
----------------------

(optional) Create a new environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is a good practice to create a specific virtual environment for the ``tqec`` package.

One way of doing that is using the native ``venv`` package of your python installation:

.. code-block:: bash

    python -m venv [path to where you want your virtual environment]/tqec
    # On GNU/Linux and MacOS
    source [path to where you want your virtual environment]/tqec/bin/activate
    # On Windows
    ## In cmd.exe
    [path to where you want your virtual environment]\tqec\Scripts\activate.bat
    ## In PowerShell
    [path to where you want your virtual environment]\tqec\Scripts\Activate.ps1

Install the ``tqec`` package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``tqec`` package is a regular Python package that can be installed using ``pip``.

It is not (yet) available on the official Python Package Index PyPI, so you will have
to manually provide the URL to install the package:

.. code-block:: bash

    python -m pip install git+https://github.com/QCHackers/tqec.git

And that's it! You can test the installation by running

.. code-block:: bash

    python -c "import tqec"

If the installation succeeded, the command should return without any message displayed.
Else, a message like

.. code-block::

    Traceback (most recent call last):
      File "<string>", line 1, in <module>
    ModuleNotFoundError: No module named 'tqec'

should appear.
