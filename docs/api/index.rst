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

.. autofunction:: pyfits._version_abi.libfits_version_packed
   :no-index:

.. autofunction:: pyfits.libfits_version_major

.. autofunction:: pyfits.api_version_minor

.. autofunction:: pyfits.libfits_version_packed

.. autofunction:: pyfits.libfits_version_string

.. autofunction:: pyfits.lib_path

Submodules
----------

.. toctree::
   :maxdepth: 1

   repo
   models
   exceptions
   schemas
