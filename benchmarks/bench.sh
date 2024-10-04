#!/bin/sh

# Exit on error of any of the following lines.
set -e

usage() {
    echo "Usage:"
    echo "\tbench.sh [value of k]"
    echo ""
    echo "Examples:"
    echo "\tbench.sh 2"
}

if [ $# -ne 1 ]
  then
    usage
    exit 1
fi

PARENT_PATH=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )

PYTHON_EXEC_NAME="cnot_all_observables"
SCALING_FACTOR="$1"
BENCH_DIRECTORY="${PARENT_PATH}/data/${PYTHON_EXEC_NAME}_k=${SCALING_FACTOR}_$(date '+%F_%H-%M-%S')"

echo "Saving all benchmark data to ${BENCH_DIRECTORY}"
mkdir -p $BENCH_DIRECTORY

echo "Statistical profiling of ${PYTHON_EXEC_NAME}.py using pyinstrument..."
python -m pyinstrument -o "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}_k=${SCALING_FACTOR}.html" -r html ${PYTHON_EXEC_NAME}.py -k "${SCALING_FACTOR}"
echo "Profiling saved as an HTML webpage in ${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}_k=${SCALING_FACTOR}.html"

CLI_OUTDIR="${BENCH_DIRECTORY}/dae2circuits/"
DAE_CNOT_FILE="$(realpath "${PARENT_PATH}/../assets/clean_exportable_cnot.dae")"
CLI_CMD="tqec dae2circuits --out-dir ${CLI_OUTDIR} -k ${SCALING_FACTOR} --add-detectors ${DAE_CNOT_FILE}"

echo "Statistical profiling of the command '${CLI_CMD}' using pyinstrument..."
python -m pyinstrument -o "${BENCH_DIRECTORY}/tqec_dae2circuits_k=${SCALING_FACTOR}.html" -r html --from-path ${CLI_CMD}
echo "Profiling saved as an HTML webpage in ${BENCH_DIRECTORY}/tqec_dae2circuits_k=${SCALING_FACTOR}.html"
echo "Results of the tqec dae2circuits command saved in '${CLI_OUTDIR}'."

# echo "Profiling ${PYTHON_EXEC_NAME}.py using cProfile..."
# python -m cProfile -o "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.pstats" ${PYTHON_EXEC_NAME}.py -k $@
# echo "cProfile information saved in ${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.pstats"

# echo "Generating graphs from profiling report..."
# python -m flameprof --width 4800 --font-size 10 "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.pstats" > "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}_flamegraph.svg"
# python -m gprof2dot -n 0 -e 0 --depth 2 -f pstats "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.pstats" > "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.dot"
# dot -Tsvg -o "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}_callgraph.svg" < "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.dot"
# dot -Tpng -o "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}_callgraph.png" < "${BENCH_DIRECTORY}/${PYTHON_EXEC_NAME}.dot"
