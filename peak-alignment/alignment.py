import trsfile
from trsfile.parametermap import TraceParameterMap, TraceParameterDefinitionMap
import trsfile.traceparameter as tp
import matplotlib.pyplot as plt
import sys
import numpy as np
from correlation import run_correlation
from tqdm import trange
from typing import Any
from docopt import docopt

doc = """

Usage: python3 alignment.py <input-file> [options]

Options:
    -h --help       Show this screen.
    -w WS           <int> The size of the alignment window in samples. [default: 500]
    -s S            <int> The start of the window in samples. [default: 0]
    -n NT           <int> The number of traces to parse. [default: 5]
"""

arguments = docopt(doc, sys.argv)


WINDOW_SIZE: int = int(arguments["-w"])
START: int = int(arguments["-s"])
NUM_OF_TRACES: int = int(arguments["-n"])
EXPORT_PATH: str = arguments["<input-file>"] + '+PEAK_ALIGN.trs'
INPUT_FILE: str = arguments["<input-file>"]
WINDOW_RESAMPLE_PATH: str = "AES_fixed_rand_input_CAFEBABEDEADBEEF0001020304050607_SAVEEVEN_0_1000_+AWR(1000,0.99).trs";

def align(traces_list: Any, diffs: Any) -> Any:
    aligned = [np.array([]) for _ in range(len(traces_list) - 1)]
    for i in range(len(traces_list) - 1):
        peak_idx = np.argmax(traces_list[i + 1][START:START + WINDOW_SIZE], axis=0) + START
        average = np.mean(traces_list[i + 1], axis=0)

        aligned[i] = np.concatenate((aligned[i], traces_list[i + 1][:START]))

        if diffs[i][0] < 0:
            aligned[i] = np.concatenate((aligned[i], np.tile(average, abs(diffs[i][0]))))
            aligned[i] = np.concatenate(
                (aligned[i], traces_list[i + 1][START: START + WINDOW_SIZE]))
        else:
            aligned[i] = np.concatenate(
                (aligned[i], traces_list[i + 1][START + diffs[i][0]: START + WINDOW_SIZE]))
        
        if (len(aligned[i]) < 220000):
            aligned[i] = np.concatenate((aligned[i], np.tile(average, 220000 - len(aligned[i]))))
        else:
            aligned[i] = aligned[:220000]
        aligned[i] = np.concatenate((aligned[i], traces_list[i + 1][START + WINDOW_SIZE:]))

    return aligned


def peak_disalignment(traces) -> Any:
    diffs = []
    template = np.argmax(traces[0][START:START+WINDOW_SIZE], axis=0)
    for i in range(1, len(traces)):
        diffs.append([])
        diffs[i - 1].append(np.argmax(traces[i][START: START + WINDOW_SIZE], axis=0) - template)
    return diffs


def plot(traces, copies) -> Any:
    _, axs = plt.subplots(2)

    # Plot the first subplot
    for i in range(NUM_OF_TRACES):
        axs[0].plot(traces[i], label='Trace ' + str(i))
    axs[0].set_title('First Subplot')
    axs[0].legend()

    # Plot the second subplot
    axs[1].plot(traces[0], label='Trace 0')
    for i in range(1, NUM_OF_TRACES):
        axs[1].plot(copies[i - 1], label='Trace ' + str(i) + '\'')
    axs[1].set_title('Second Subplot')
    axs[1].legend()

    plt.tight_layout()  # Adjust layout to prevent overlap
    plt.show()


def create_trs() -> None:
    data = []
    with trsfile.trs_open(INPUT_FILE, 'r', enigine='TrsEngine') as traces:
        with trsfile.trs_open(EXPORT_PATH, 'w', headers={
            trsfile.Header.TRS_VERSION: 2,
            trsfile.Header.DESCRIPTION: "Copied",
            trsfile.Header.SCALE_X: traces.get_headers().get(trsfile.Header.SCALE_X),
            trsfile.Header.SCALE_Y: traces.get_headers().get(trsfile.Header.SCALE_Y),
            trsfile.Header.TRACE_PARAMETER_DEFINITIONS: TraceParameterDefinitionMap(
                {'LEGACY_DATA': tp.TraceParameterDefinition(tp.ParameterType.BYTE, 32, 0)})
        }, padding_mode=trsfile.TracePadding.AUTO, live_update=True,
                              engine='TrsEngine') as new_traces:
            for i in trange(NUM_OF_TRACES):
                if i == 0:
                    if WINDOW_RESAMPLE_PATH == "" :
                        data.append(np.array(traces[0].samples))
                    else:
                        with trsfile.trs_open(WINDOW_RESAMPLE_PATH, 'r', engine='TrsEngine') as resample:
                            data.append(np.array(resample[0].samples))
                        data.append(np.array(traces[0].samples))
                        aligned = align(np.array(data), peak_disalignment(np.array(data)))[0]
                else:
                    data.append(np.array(traces[i].samples))
                    aligned = align(np.array(data), peak_disalignment(np.array(data)))[0]
                # Adding one Trace
                new_traces.append(
                    trsfile.Trace(
                        trsfile.SampleCoding.FLOAT,
                        data[0] if i == 0 and WINDOW_RESAMPLE_PATH == "" else aligned,
                        TraceParameterMap({'LEGACY_DATA': tp.ByteArrayParameter(
                            bytes(traces[i].parameters['LEGACY_DATA'].value))}),
                    )
                )
                if len(data) > 1:
                    data.pop()


def main() -> None:
    create_trs()
    run_correlation(EXPORT_PATH)


if __name__ == "__main__":
    main()
