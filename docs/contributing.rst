How to contribute
=================

Installation procedure (for developers)
---------------------------------------

If you want to help maintaining and improving the ``tqec`` package, you will need
to install a few more packages than the regular installation. It is also
recommended to use an editable installation.

.. code-block:: bash

    # Clone the repository to have local files to work on
    git clone https://github.com/QCHackers/tqec.git
    # Install the library with developer dependencies
    python -m pip install -e 'tqec[all]'
    # Go in the tqec directory and enable pre-commit
    cd tqec
    pre-commit install

You can now start contributing, following the rules explained in the next sections.
