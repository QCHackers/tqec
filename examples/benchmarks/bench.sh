#!/bin/sh

# Exit on error of any of the following lines.
set -e

usage() {
    echo "Usage:"
    echo "\tbench.sh [python file] [value of k]"
    echo ""
    echo "Examples:"
    echo "\tbench.sh cnot_all_observables.py 2"
}

if [ $# -ne 2 ]
  then
    usage
    exit 1
fi

PYTHON_EXEC_NAME=$(basename "$1" .py)
SCALING_FACTOR="$2"
BENCH_DIRECTORY="data/${PYTHON_EXEC_NAME}_k=${SCALING_FACTOR}_$(date '+%F_%H-%M-%S')"

echo "Saving all benchmark data to ${BENCH_DIRECTORY}"
mkdir -p $BENCH_DIRECTORY

echo "Statistical profiling of ${PYTHON_EXEC_NAME}.py using pyinstrument..."
python -m pyinstrument -o "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}_k=${SCALING_FACTOR}.html" -r html ${PYTHON_EXEC_NAME}.py -k "$2"
echo "Profiling saved as an HTML webpage in ${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}_k=${SCALING_FACTOR}.html"

# echo "Profiling ${PYTHON_EXEC_NAME}.py using cProfile..."
# python -m cProfile -o "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.pstats" ${PYTHON_EXEC_NAME}.py -k $@
# echo "cProfile information saved in ${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.pstats"

# echo "Generating graphs from profiling report..."
# python -m flameprof --width 4800 --font-size 10 "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.pstats" > "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}_flamegraph.svg"
# python -m gprof2dot -n 0 -e 0 --depth 2 -f pstats "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.pstats" > "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.dot"
# dot -Tsvg -o "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}_callgraph.svg" < "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.dot"
# dot -Tpng -o "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}_callgraph.png" < "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.dot"
