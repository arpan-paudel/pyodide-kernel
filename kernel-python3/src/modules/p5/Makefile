build: minify
	python3 setup.py sdist bdist_wheel

minify:
	npx gulp all

clean:
	rm -rf *.egg-info/ build/ dist/ p5/p5.min.js*

.PHONY: build clean minify
