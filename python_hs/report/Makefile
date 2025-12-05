SRC_DIR := ../python_hs
SRC_FILES := $(wildcard $(SRC_DIR)/*)

BENCHMARKS := nemo-audio-processing rainbowcake-python-video-processing bioinfo-automine biostars-multiprocessing kaggle-captk-brats-preprocessing
MULTI_BENCHMARKS := nemo-audio-processing biostars-multiprocessing
BAD_BENCHMARKS := biostars-multiprocessing

results = $(foreach t,$(2),results/$(t)-$(1).json)

ALL_JSON_RESULTS := \
  $(call results,nemo-audio-processing,multi spec sub) \
  $(call results,rainbowcake-python-video-processing,spec sub) \
  $(call results,bioinfo-automine,spec sub) \
  $(call results,biostars-multiprocessing,multi spec sub bad_spec) \
  $(call results,kaggle-captk-brats-preprocessing,multi spec sub)

.PHONY: all clean clean_data download-tools download-data download-all

all: plots/runtimes_plot.png

download-tools: tools/.downloaded

tools/.downloaded:
	./download_tools

data/%/.downloaded: benchmarks/%/download_data tools/.downloaded | data/
	cd benchmarks/$* && ./download_data

define type_rule
results/$(1)-%.md results/$(1)-%.json &: tools/.downloaded data/%/.downloaded $$(SRC_FILES) | results/
	./benchmark.sh $(1) $$* results/
endef
$(foreach t,sub spec multi bad_spec,$(eval $(call type_rule,$(t))))

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

download-data: $(foreach bench,$(BENCHMARKS),data/$(bench)/.downloaded)
download-all: download-tools download-data
