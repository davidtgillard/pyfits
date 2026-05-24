API overview
============

Public exports from the ``pyfits`` package:

.. currentmodule:: pyfits

Classes and types
-----------------

* :doc:`repo` — :class:`~pyfits.repo.Repo` session API
* :doc:`models` — graph and validation models (:class:`~pyfits.models.Id`, :class:`~pyfits.models.ValidateResult`, …)
* :doc:`exceptions` — :class:`~pyfits._errors.FitsError`, :class:`~pyfits._errors.FitsSchemaError`, :class:`~pyfits._errors.FitsStatus`
* :doc:`schemas` — JSON Schema access helpers

Version and library info
------------------------

.. autoclass:: pyfits.Version
   :members:
   :exclude-members: major, minor, patch, version_string

.. autofunction:: pyfits.get_version

Submodules
----------

.. toctree::
   :maxdepth: 1

   repo
   models
   exceptions
   schemas
