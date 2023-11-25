build: extern
	python3 setup.py sdist bdist_wheel

extern:
	mkdir -p extern/
	npx gulp -f extern-build/gulpfile.js all

clean:
	rm -rf *.egg-info/ build/ dist/ extern/

.PHONY: build clean extern
