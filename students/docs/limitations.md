# Limitations and Future Improvements

## Current limitations

- Synthetic data is used by design for demo purposes.
- Historical labeled outcome models are not yet implemented.
- Authentication is a prototype-only demo layer.
- The import mechanism validates structure but does not yet persist uploaded records to a full database layer.

## Future improvements

- Save uploaded records to SQLite or PostgreSQL with provenance tracking.
- Support a real ML model for academic failure or placement outcome prediction using historical labels.
- Add detailed faculty and student role-specific permissioning.
- Introduce exportable and downloadable reports with more granular filters.
- Add a richer audit trail and intervention tracking workflow.
