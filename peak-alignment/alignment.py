import trsfile
from trsfile.parametermap import TraceParameterMap, TraceParameterDefinitionMap
import trsfile.traceparameter as tp
import sys
import numpy as np
from numpy import concatenate as cat
from correlation import run_correlation
from tqdm import trange
from typing import Any
from docopt import docopt
from scipy.stats import pearsonr
import math

doc = """
Usage: python3 alignment.py <input-file> [options]

Options:
    -h --help       Show this screen.
    -w WS               <int> The size of the alignment window in samples. [default: 500]
    -s S                <int> The start of the window in samples. [default: 0]
    -n NT               <int> The number of traces to parse. [default: 5]
    -r WRP              <str> Path to the traces with absolute window resample. [default: ]
    -c COR              <bool> If true, peak each trace. [default: ]
"""

arguments = docopt(doc, sys.argv)

WINDOW_SIZE: int = int(arguments["-w"])
START: int = int(arguments["-s"])
NUM_OF_TRACES: int = int(arguments["-n"])
EXPORT_PATH: str = arguments["<input-file>"] + '+PEAK_ALIGN.trs'
INPUT_FILE: str = arguments["<input-file>"]
WINDOW_RESAMPLE_PATH: str = arguments["-r"]
CORRELATION: bool = arguments["-c"]


def align(traces_list: Any, diffs: Any) -> Any:
    """
    Aligns the traces
    :param traces_list: The trace data to align
    :param diffs: The offsets each trace is offset by
    :return: a modified traces_list that is aligned.
    """
    aligned = [np.array([]) for _ in range(len(traces_list) - 1)]
    for i in range(len(traces_list) - 1):
        average = np.mean(traces_list[i + 1], axis=0)

        aligned[i] = cat((aligned[i], traces_list[i + 1][:START]))

        if diffs[i][0] < 0:
            aligned[i] = cat((aligned[i], np.tile(average, abs(diffs[i][0]))))
            aligned[i] = cat((aligned[i], traces_list[i + 1][START: START + WINDOW_SIZE]))
        else:
            aligned[i] = cat((aligned[i], traces_list[i + 1][START + diffs[i][0]: START + WINDOW_SIZE]))

        aligned[i] = cat((aligned[i], traces_list[i + 1][START + WINDOW_SIZE:]))

        if len(aligned[i]) < 220000:
            aligned[i] = cat((aligned[i], np.tile(average, 220000 - len(aligned[i]))))
        else:
            aligned[i] = aligned[i][0:220000]

    return aligned


def peak_alignment(traces) -> Any:
    """
    Calculates peak misalignment in regard to trace [0] from traces for each trace.
    :param traces: A numpy array containing trace data.
    :return: The offsets required by the align algorithm
    """
    diffs = []
    template = np.argmax(traces[0][START:START + WINDOW_SIZE], axis=0)
    for i in range(1, len(traces)):
        # The 0th trace needs to be inserted
        diffs.append([])
        diffs[i - 1].append(np.argmax(traces[i][START: START + WINDOW_SIZE], axis=0) - template)
    return diffs


def correlation_alignment(data):
    """
    Runs a series of correlation calculations on provided data
    For each pair of traces we calculate the correlation between them.
    More importantly, we calculate the difference by which each two traces are
    offset from one-another.

    :param data: A numpy array containing trace data.
    :return: The offsets required by the align algorithm
    """
    maximum = 0
    max_location = (0, 0)
    global START
    if START == 0:
        for i in trange(WINDOW_SIZE,
                        math.trunc((len(data[0]) * 0.9)),
                        1000):
            for j in range(max(i - WINDOW_SIZE, 0),
                           min(len(data[1]) - WINDOW_SIZE, i + WINDOW_SIZE),
                           10):
                sol = abs(pearsonr(data[0][i:i + WINDOW_SIZE], data[1][j:j + WINDOW_SIZE]).statistic)
                if sol > maximum:
                    max_location = (i, j)
                    maximum = sol
                    START = i
    else:
        for j in range(max(START - WINDOW_SIZE, 0),
                       min((len(data[1]) - WINDOW_SIZE),
                           START + WINDOW_SIZE), 10):
            sol = abs(pearsonr(data[0][START:START + WINDOW_SIZE], data[1][j:j + WINDOW_SIZE]).statistic)
            if sol > maximum:
                max_location = (START, j)
                maximum = sol
    dif = [[max_location[1] - max_location[0]]]
    return dif


def create_trs() -> None:
    """
    Open a TRS file provided in the CLI arguments
    Call the align functions it according to a selected analysis
    Output the aligned files for viewing

    :return: Nothing - just performs said steps
    """
    data = []
    # Opening input
    with trsfile.trs_open(INPUT_FILE, 'r', enigine='TrsEngine') as traces:

        with trsfile.trs_open(EXPORT_PATH, 'w', headers=form_header(traces),
                              padding_mode=trsfile.TracePadding.AUTO,
                              live_update=True, engine='TrsEngine') as new_traces:

            # Go through the number of traces set by the user
            # Aligning by the selected method
            for i in trange(NUM_OF_TRACES):
                if i == 0:
                    aligned = deal_with_zero_trace(data, traces)
                else:
                    data.append(np.array(traces[i].samples))
                    if CORRELATION:
                        dif = correlation_alignment(np.array(data))
                        aligned = (np.array(data), dif)[0]
                    else:
                        aligned = align(np.array(data), peak_alignment(np.array(data)))[0]

                new_traces.append(form_new_trace(aligned, data, i, traces))
                if len(data) > 1:
                    data.pop()


def form_header(traces):
    """
    A standardized set of headers, copied from the input file, adjusted for
    the needs of the output
    :param traces: Input file
    :return: A formed trs header
    """
    h = trsfile.Header
    return {
        h.TRS_VERSION: 2,
        h.DESCRIPTION: "Copied",
        h.SCALE_X: traces.get_headers().get(h.SCALE_X),
        h.SCALE_Y: traces.get_headers().get(h.SCALE_Y),
        h.TRACE_PARAMETER_DEFINITIONS: TraceParameterDefinitionMap(
            {'LEGACY_DATA': tp.TraceParameterDefinition(tp.ParameterType.BYTE, 32, 0)})
    }


def form_new_trace(aligned, data, i, traces):
    """
    Helper function to form a trace to be appended
    :param aligned: The aligned data
    :param data: The original data
    :param i: The index of the trace being appended
    :param traces: Open input file
    :return: a formed trace ready to be appended to the ouptup
    """
    if i == 0 and WINDOW_RESAMPLE_PATH == "":
        return trsfile.Trace(trsfile.SampleCoding.FLOAT, data[0],
                             TraceParameterMap({'LEGACY_DATA': tp.ByteArrayParameter(
                                 bytes(traces[i].parameters['LEGACY_DATA'].value))}))
    return trsfile.Trace(trsfile.SampleCoding.FLOAT, aligned,
                         TraceParameterMap({'LEGACY_DATA': tp.ByteArrayParameter(
                             bytes(traces[i].parameters['LEGACY_DATA'].value))}))


def deal_with_zero_trace(data, traces):
    """
    Helper function to deal with potential misalignment
    The 0th trace usually remains unchanged and is thus
    treated differently
    :param data: The original data
    :param traces: The original data
    :return:
    """
    aligned = None
    if WINDOW_RESAMPLE_PATH == "":
        data.append(np.array(traces[0].samples))
    else:
        with trsfile.trs_open(WINDOW_RESAMPLE_PATH, 'r', engine='TrsEngine') as resample:
            data.append(np.array(resample[0].samples))

        data.append(np.array(traces[0].samples))
        aligned = align(np.array(data), peak_alignment(np.array(data)))[0]
    return aligned


def main() -> None:
    create_trs()

    run_correlation(EXPORT_PATH)


if __name__ == "__main__":
    main()
