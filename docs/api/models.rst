Models
======

.. autoclass:: pyfits.models.Id
   :members:
   :exclude-members: value
   :show-inheritance:

.. autoclass:: pyfits.models.TargetId
   :members:
   :exclude-members: value
   :show-inheritance:

.. autoclass:: pyfits.models.ObjectTypeName
   :members:
   :exclude-members: value
   :show-inheritance:

.. autoclass:: pyfits.models.Graph
   :members:
   :exclude-members: nodes, edges
   :show-inheritance:

.. autoclass:: pyfits.models.GraphNode
   :members:
   :exclude-members: id, parent_id
   :show-inheritance:

.. autoclass:: pyfits.models.GraphEdge
   :members:
   :exclude-members: from_id, to_id, kind, link_type, id, parent_id
   :show-inheritance:

.. autoclass:: pyfits.models.ValidationIssue
   :members:
   :exclude-members: severity, code, message, object_id
   :show-inheritance:

.. autoclass:: pyfits.models.ValidateSummary
   :members:
   :exclude-members: total_validation_issues, info_count, warning_count, error_count
   :show-inheritance:

.. autoclass:: pyfits.models.ValidateResult
   :members:
   :exclude-members: validation_issues, summary, protocol_version
   :show-inheritance:
