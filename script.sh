export PYTHONPATH=$(pwd):$PYTHONPATH

TEST_AQUA_BENCHMARK_DIRECTORY='tmp/tests/aqua_benchmark' python3 benchmark.py \
--gold_sql aqua_benchmark_dataset.yml \
--pred_sql tmp/tests/aqua_benchmark/ \
--gold_res tmp/tests/aqua_benchmark/ \
--pred_res tmp/tests/aqua_benchmark/ \
--table mocked_data/tables.json \
--etype exec