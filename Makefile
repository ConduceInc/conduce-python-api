
deps: setup-env deps-venv2 deps-venv3

setup-env: install-pythons venv2 venv3 

PY2VER = 2.7.16
PY3VER = 3.7.4

install-pythons: install-python2 install-python3

install-python2:
	@if ! pyenv versions | grep -q $(PY2VER) ;\
		then pyenv install $(PY2VER) ;\
		PYENV_VERSION=$(PY2VER) pyenv exec pip install --upgrade pip ;\
		fi
	@if ! PYENV_VERSION=$(PY2VER) pyenv exec pip list | grep virtualenv ;\
		then PYENV_VERSION=$(PY2VER) pyenv exec pip install virtualenv ;\
		fi

install-python3:
	pyenv install -s $(PY3VER)

venv2:
	mkdir -p venv2
	$(eval PYVER=`PYENV_VERSION=$(PY2VER) pyenv exec python -c "import sys;t='{v[0]}.{v[1]}.{v[2]}'.format(v=list(sys.version_info[:3]));sys.stdout.write(t)"`)
	@if [ $(PYVER) != $(PY2VER) ] ;\
		then echo "ERROR: pyenv not configured correctly, check your configuration" ;\
		exit 1 ;\
		fi
	PYENV_VERSION=$(PY2VER) pyenv exec virtualenv venv2
	$(eval PYVENV=`./venv2/bin/python -c "import sys;t='{v[0]}.{v[1]}.{v[2]}'.format(v=list(sys.version_info[:3]));sys.stdout.write(t)"`)
	@if [ "$(PYVENV)" != $(PY2VER) ] ;\
		then echo "ERROR: virtual environment has wrong python version, check your system configuration" ;\
		exit 1 ;\
		fi

venv3:
	mkdir -p venv3
	$(eval PYVER=`PYENV_VERSION=$(PY3VER) pyenv exec python -c "import sys;t='{v[0]}.{v[1]}.{v[2]}'.format(v=list(sys.version_info[:3]));sys.stdout.write(t)"`)
	@if [ $(PYVER) != $(PY3VER) ] ;\
		then echo "ERROR: pyenv not configured correctly, check your configuration" ;\
		exit 1 ;\
		fi
	PYENV_VERSION=$(PY3VER) pyenv exec python -m venv venv3
	$(eval PYVENV=`./venv3/bin/python -c "import sys;t='{v[0]}.{v[1]}.{v[2]}'.format(v=list(sys.version_info[:3]));sys.stdout.write(t)"`)
	@if [ "$(PYVENV)" != $(PY3VER) ] ;\
		then echo "ERROR: virtual environment has wrong python version, check your system configuration" ;\
		exit 1 ;\
		fi

deps-venv2: venv2 requirements-dev.txt
	./venv2/bin/pip install -r requirements-dev.txt

deps-venv3: venv3 requirements-dev.txt
	./venv3/bin/pip install --upgrade pip
	./venv3/bin/pip install -r requirements-dev.txt

devtest: clean-pyc devtest2 devtest3

test: clean-pyc test2 test3

devtest2:
	./venv2/bin/python -m unittest discover -v test/

devtest3:
	./venv3/bin/python -m unittest discover -v test/

test2:
	./venv2/bin/python -m unittest discover -v test/ -b

test3:
	./venv3/bin/python -m unittest discover -v test/ -b

docs: venv3 
	. ./venv3/bin/activate && make -C doc html

clean-pyc:
	find . -name '*.pyc' | xargs rm -f
	find . -name '*.pyo' | xargs rm -f

clean: clean-pyc
	rm -rf venv2
	rm -rf venv3
