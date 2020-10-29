venv:
	python3 -m venv venv

requirements:
	pip install -r requirements.txt

tools:
	pip install -r tools.txt

init: requirements tools
	pip install -e .

lwip_lib:
	mkdir -p lwip_lib/build && cd lwip_lib/build && cmake .. && make -s all 

clean:
	cd lwip_lib/build && make -s clean

.PHONY: init tools requirements clean lwip_lib venv
