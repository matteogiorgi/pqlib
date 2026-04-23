CC := gcc
CFLAGS := -std=c11 -Wall -Wextra -pedantic


TARGET := binaryheap.o
TARGET_RUN := binaryheap_demo
TARGET_TEST := binaryheap_test
SRC := binaryheap.c
SRC_DEMO := binaryheap_demo.c
SRC_TEST := binaryheap_test.c
HEADER := binaryheap.h
.PHONY: all clean run test


all: $(TARGET)

$(TARGET): $(SRC) $(HEADER)
	$(CC) $(CFLAGS) -c $(SRC) -o $(TARGET)

$(TARGET_RUN): $(SRC) $(SRC_DEMO) $(HEADER)
	$(CC) $(CFLAGS) $(SRC) $(SRC_DEMO) -o $(TARGET_RUN)

$(TARGET_TEST): $(SRC) $(SRC_TEST) $(HEADER)
	$(CC) $(CFLAGS) $(SRC) $(SRC_TEST) -o $(TARGET_TEST)

run: $(TARGET_RUN)
	./$(TARGET_RUN)

test: $(TARGET_TEST)
	./$(TARGET_TEST)

clean:
	rm -f $(TARGET) $(TARGET_RUN) $(TARGET_TEST)
