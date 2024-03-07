# BPM Diagram Converter

A Python tool to convert BPM diagrams to the Graphviz dot format

## Installation

Note: on Windows the step for activating the virtual environment should be changed from `source venv/bin/activate` to `venv\Scripts\activate.bat`

### From source

```shell
git clone https://github.com/madeye-matt/bpm_diagram_madeye
cd bpm_diagram_madeye
python -v venv venv
source venv/bin/activate
pip install requirements.txt
```

### From binaries

Go to the [releases page on GitHub](https://github.com/madeye-matt/bpm_diagram_madeye/releases) and download the latest wheel (.whl) file

```shell
mkdir bpm_diagram_madeye
wget https://github.com/madeye-matt/bpm_diagram_madeye/releases/download/0.1.0/bpm_diagram_madeye-0.1.0-py3-none-any.whl
python -v venv venv
source venv/bin/activate
pip install bpm_diagram_madeye-0.1.0-py3-none-any.whl
```

## Running

### From source

```shell
cd bpm_diagram_madeye
source venv/bin/activate
python -m bpm_diagram_madeye.bpm_diagram --help
python -m bpm_diagram_madeye.bpm_diagram some-bpm-file.bpmn -o some-bpm-file.gz
```

### From binaries

```shell
cd bpm_diagram_madeye
source venv/bin/activate
bpm_diagram --help
python -m bpm_diagram_madeye.bpm_diagram some-bpm-file.bpmn -o some-bpm-file.gz
```

### Parameters

```
usage: bpm_diagram [-h] [-o OUTPUT_FILE] [--exception-subprocess-name EXCEPTION_SUBPROCESS_NAME] [--show-flows | --no-show-flows] [--show-package-names | --no-show-package-names]
                   [--show-error-handling | --no-show-error-handling] [--show-task-listeners | --no-show-task-listeners]
                   input_file

Creates a dot/graphviz diagram from a BPMN file

positional arguments:
  input_file            The BPMN file to process

options:
  -h, --help            show this help message and exit
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        The .dot file to write the diagram to
  --exception-subprocess-name EXCEPTION_SUBPROCESS_NAME
                        The name of the subprocess for handling exceptions
  --show-flows, --no-show-flows
                        Show the flow name on the edge label
  --show-package-names, --no-show-package-names
                        Show the package names for Java classes
  --show-error-handling, --no-show-error-handling
                        Show error handling (adds much complexity)
  --show-task-listeners, --no-show-task-listeners
                        Show task listeners for userTasks
```

## How to create something useful from the output?

This utility converts a BPM diagram in XML form into a graph in [the DOT language](https://en.wikipedia.org/wiki/DOT_(graph_description_language)).  In order to visualise the diagram this graph needs to be converted into PDF or PNG or similar by using the [Graphviz tool](https://graphviz.org/).

- [Download and/or install](https://graphviz.org/download/) the relevant version of the graphviz tool for your operating system
- Run one of the following commands to convert the output from the `bpm_diagram` utility to a format that can be visualised

### PDF

```shell
dot -Tpdf some-bpm-file.bpmn -o some-bpm-file.pdf
```

### PNG 

```shell
dot -Tpng some-bpm-file.bpmn -o some-bpm-file.png
```

### Other

`dot` supports a myriad of output formats which can be selected by varying the `-T` parameter on the above commands.  A full list can be found on the [Graphviz website](https://graphviz.org/docs/outputs/)

## Issues

This utility was developed to parse specific examples of Activiti created diagrams.  It may or may not work on diagrams created for other platforms.  Additionally, it wil only work for diagrams with a single `bpmn:process`.  This is on account of an incorrect assumption based on the diagrams it was designed to work with.   A version without this limitation is top of the TODO list.
