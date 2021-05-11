SHELL=/bin/bash
PYTHON=python3
PYTHON_VENV=env

.PHONY: clean doc

# environment #################################################################
$(PYTHON_VENV)/.created: REQUIREMENTS.txt
	rm -rf $(PYTHON_VENV) && \
	$(PYTHON) -m venv $(PYTHON_VENV) && \
	. $(PYTHON_VENV)/bin/activate && \
	pip install pip --upgrade && \
	pip install -r ./REQUIREMENTS.txt && \
	date > $(PYTHON_VENV)/.created

env: $(PYTHON_VENV)/.created

clean:
	rm -rf $(PYTHON_VENV) .tox

# packaging ###################################################################
test: env
	. $(PYTHON_VENV)/bin/activate && \
	tox $(args)
