CC := gcc
CFLAGS := -std=c99 -Wall -Wextra -pedantic
CPPFLAGS := -Iinclude -Isrc


BUILD_DIR := build
LIB := $(BUILD_DIR)/libpqlib.a
TARGET_RUN := $(BUILD_DIR)/priority_queue_demo
TARGET_TEST := $(BUILD_DIR)/priority_queue_test
SRC := src/priority_queue.c src/heaps/binary_heap.c src/skiplists/randomized_skiplist.c
OBJ := $(SRC:%.c=$(BUILD_DIR)/%.o)
SRC_DEMO := examples/priority_queue_demo.c
SRC_TEST := tests/priority_queue_test.c
PUBLIC_HEADERS := include/pqlib/priority_queue.h
INTERNAL_HEADERS := src/priority_queue_internal.h src/heaps/binary_heap.h src/skiplists/randomized_skiplist.h
.PHONY: all clean run test python-build python-test wheel release release-upload


all: $(LIB)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/%.o: %.c $(PUBLIC_HEADERS) $(INTERNAL_HEADERS) | $(BUILD_DIR)
	mkdir -p $(dir $@)
	$(CC) $(CPPFLAGS) $(CFLAGS) -c $< -o $@

$(LIB): $(OBJ)
	ar rcs $(LIB) $(OBJ)

$(TARGET_RUN): $(SRC_DEMO) $(LIB) $(PUBLIC_HEADERS)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SRC_DEMO) $(LIB) -o $(TARGET_RUN)

$(TARGET_TEST): $(SRC_TEST) $(LIB) $(PUBLIC_HEADERS)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(SRC_TEST) $(LIB) -o $(TARGET_TEST)

run: $(TARGET_RUN)
	./$(TARGET_RUN)

test: $(TARGET_TEST)
	./$(TARGET_TEST)

python-build:
	python3 setup.py build_ext --inplace

python-test: python-build
	python3 tests/python_priority_queue_test.py
	python3 tests/learning_augmented_priority_queue_test.py

wheel:
	python3 -m pip wheel . --no-deps --no-build-isolation -w dist

release:
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make release VERSION=0.1.0"; \
		exit 2; \
	fi
	scripts/release.sh $(VERSION)

release-upload:
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make release-upload VERSION=0.1.0 [REPO=OWNER/REPO]"; \
		exit 2; \
	fi
	@if [ -n "$(REPO)" ]; then \
		scripts/release.sh $(VERSION) --upload --repo $(REPO); \
	else \
		scripts/release.sh $(VERSION) --upload; \
	fi

clean:
	rm -rf $(BUILD_DIR)
	rm -rf dist
	rm -rf pqlib.egg-info
	rm -f pqlib*.so
	rm -rf tests/__pycache__
	rm -rf tests/pq_experiments/__pycache__
