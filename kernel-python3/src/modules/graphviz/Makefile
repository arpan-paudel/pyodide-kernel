build: minify
	python3 setup.py sdist bdist_wheel

minify:
	npx gulp all

clean:
	rm -rf *.egg-info/ build/ dist/ graphviz/viz.min.js*

.PHONY: build clean minify
