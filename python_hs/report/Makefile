SRC_DIR := ../python_hs
BENCHMARKS := $(patsubst benchmarks/%/,%,$(wildcard benchmarks/*/))
MULTI_BENCHMARKS := $(patsubst benchmarks/%/multiprocess.py,%,$(wildcard benchmarks/*/multiprocess.py))

SRC_FILES := $(wildcard $(SRC_DIR)/*)

ALL_JSON_RESULTS := $(foreach bench,$(BENCHMARKS),results/sub-$(bench).json results/spec-$(bench).json)
ALL_JSON_RESULTS += $(foreach bench,$(MULTI_BENCHMARKS),results/multi-$(bench).json)

.PHONY: all clean clean_data download-tools

all: plots/runtimes_plot.png

download-tools: tools/.downloaded

tools/.downloaded:
	./download_tools

data/%/.downloaded: benchmarks/%/download_data tools/.downloaded | data/
	cd benchmarks/$* && ./download_data

define type_rule
results/$(1)-%.md results/$(1)-%.json &: data/%/.downloaded $$(SRC_FILES) | results/
	./benchmark.sh $(1) $$* results/
endef
$(foreach t,sub spec multi,$(eval $(call type_rule,$(t))))

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
