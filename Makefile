CC := gcc
CFLAGS := -std=c11 -Wall -Wextra -pedantic


TARGET := binaryheap.o
RUN_TARGET := binaryheap_demo
TEST_TARGET := test_binaryheap
SRC := binaryheap.c
SRC_DEMO := binaryheap_demo.c
SRC_TEST := binaryheap_test.c
HEADER := binaryheap.h
.PHONY: all clean run test


all: $(TARGET)

$(TARGET): $(SRC) $(HEADER)
	$(CC) $(CFLAGS) -c $(SRC) -o $(TARGET)

$(RUN_TARGET): $(SRC) $(SRC_DEMO) $(HEADER)
	$(CC) $(CFLAGS) $(SRC) $(SRC_DEMO) -o $(RUN_TARGET)

$(TEST_TARGET): $(SRC) $(SRC_TEST) $(HEADER)
	$(CC) $(CFLAGS) $(SRC) $(SRC_TEST) -o $(TEST_TARGET)

run: $(RUN_TARGET)
	./$(RUN_TARGET)

test: $(TEST_TARGET)
	./$(TEST_TARGET)

clean:
	rm -f $(TARGET) $(RUN_TARGET) $(TEST_TARGET)
