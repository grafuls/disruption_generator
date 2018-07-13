.. highlight:: shell

============
Installation
============

Disruption Generator has a couple of prerequisites that need to be satisfied first.

Most of the instructions below assume you are running a Linux or Mac system,
but are otherwise very generic.

Prerequisites
=============

Python + pipenv
---------------
Disruption Generator currently requires Python 3.5 or higher to run. Please install Python via
the package manager of your operating system if it is not included already.

We use ``pipenv`` for installing additional modules that are not shipped with your operating 
system, or shipped in an old version, and we will make use of it during development. Please install
``pipenv`` via the package manager of your operating system if necessary.
For more info on how to start with development, go ahead to our :ref:`getting-started-label` guide.

From sources
============

The sources for Disruption Generator can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/grafuls/disruption_generator

Or download the `tarball`_:

.. code-block:: console

    $ curl -OL https://github.com/grafuls/disruption_generator/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/grafuls/disruption_generator
.. _tarball: https://github.com/grafuls/disruption_generator/tarball/master
