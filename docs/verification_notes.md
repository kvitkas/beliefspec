# Verification Notes

Model verification is produced by `pytest tests/test_model.py tests/test_leakage.py`.

The slowest debug check is
`test_tiny_actual_dataset_subset_fit_check_records_control_and_predictive_results`.
It trains the unmodified `MemoryModel` on three real generated MiniGrid Memory
episodes with labels key, ball, and unknown. The saved JSON artifact records the
number of updates, elapsed seconds, task loss, prediction loss, final fit
accuracy, and whether each variant met the debug criterion. A failed criterion is
recorded as evidence for investigation rather than hidden by changing the model
or the budget.
