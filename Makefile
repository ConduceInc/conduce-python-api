
deps: setup-env deps-venv2 deps-venv3

setup-env: venv2 venv3 

venv2:
	mkdir -p venv2
	pyenv install -s 2.7.16
ifneq "$(shell PYENV_VERSION=2.7.16 python -V 2>&1)" "Python 2.7.16"
	echo "pyenv not configured correctly, check your configuration"
	exit 1
endif
	PYENV_VERSION=2.7.16 virtualenv venv2

venv3:
	mkdir -p venv3
	pyenv install -s 3.7.4
ifneq "$(shell PYENV_VERSION=3.7.4 python -V 2>&1)" "Python 3.7.4"
	echo "pyenv not configured correctly, check your configuration"
	exit 1
endif
	PYENV_VERSION=3.7.4 python -m venv venv3

deps-venv2: venv2 requirements-dev.txt
	./venv2/bin/pip install -r requirements-dev.txt

deps-venv3: venv3 requirements-dev.txt
	./venv3/bin/pip install --upgrade pip
	./venv3/bin/pip install -r requirements-dev.txt

test: clean-pyc test2 test3

test2:
	./venv2/bin/python -m unittest discover -v test/

test3:
	./venv3/bin/python -m unittest discover -v test/

docs: venv3 
	. ./venv3/bin/activate && make -C doc html

clean-pyc:
	find . -name '*.pyc' | xargs rm -f
	find . -name '*.pyo' | xargs rm -f

clean: clean-pyc
	rm -rf venv2
	rm -rf venv3
