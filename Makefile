PACKAGE=parse_logs

run:
	python parse_logs/main.py --get-days --get-amount --verbose

format:
	isort --atomic ${PACKAGE} && black ${PACKAGE} && flake8 ${PACKAGE}
