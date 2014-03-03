UI_FILES := $(wildcard *.ui)

all: $(UI_FILES:.ui=_auto.py)

%_auto.py: %.ui
	pyside-uic $^ -o $@


