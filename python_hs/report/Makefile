SRC_DIR := ../python_hs
BENCHMARKS := $(patsubst benchmarks/%/,%,$(wildcard benchmarks/*/))
TYPES := sub spec

SRC_FILES := $(wildcard $(SRC_DIR)/*)
ALL_JSON_RESULTS := $(foreach type,$(TYPES),$(foreach bench,$(BENCHMARKS),results/$(type)-$(bench).json))

.PHONY: all clean clean_data

all: plots/runtimes_plot.png

data/%/.downloaded: benchmarks/%/download_data.sh | data/
	cd benchmarks/$* && ./download_data.sh

results/sub-%.md results/sub-%.json &: data/%/.downloaded $(SRC_FILES) | results/
	./benchmark.sh sub $* results/

results/spec-%.md results/spec-%.json &: data/%/.downloaded $(SRC_FILES) | results/
	./benchmark.sh spec $* results/

results/processed.json: $(ALL_JSON_RESULTS) process_results.py | results/
	./process_results.py

plots/runtimes_plot.png: results/processed.json runtime_plot.py | plots/
	./runtime_plot.py -o $@ results/processed.json

benchmark_table.tex: table.py benchmarks/**/*.py data/*/.downloaded
	./table.py > benchmark_table.tex

data/ results/ plots/:
	mkdir -p $@
clean:
	rm -rf results/ plots/ output/

clean_data:
	rm -rf data/
