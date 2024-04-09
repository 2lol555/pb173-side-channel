import trsfile
from trsfile.parametermap import TraceParameterMap, TraceParameterDefinitionMap 
from trsfile.traceparameter import ByteArrayParameter, ParameterType, TraceParameterDefinition
import trsfile.traceparameter as tp
import matplotlib.pyplot as plt
import sys
import numpy as np
import os
from correlation import run_correlation
from tqdm import trange

WINDOW_SIZE = 500
START = 25000
NUM_OF_TRACES = 1000
EXPORT_PATH = 'trace-set.trs'


def align(traces_list, diffs):
    aligned = [np.array([]) for _ in range(len(traces_list) - 1)]
    for i in range(len(traces_list) - 1):
        peak_idx = np.argmax(traces_list[i + 1], axis=0)
        average = np.mean(traces_list[i + 1], axis=0)

        aligned[i] = np.concatenate((aligned[i], traces_list[i + 1][:peak_idx - WINDOW_SIZE]))

        if diffs[i][0] < 0:
            aligned[i] = np.concatenate((aligned[i], np.tile(average, abs(diffs[i][0]))))
            aligned[i] = np.concatenate((aligned[i], traces_list[i + 1][peak_idx - WINDOW_SIZE: peak_idx + WINDOW_SIZE]))
        else:
            aligned[i] = np.concatenate((aligned[i], traces_list[i + 1][peak_idx - WINDOW_SIZE + diffs[i][0]: peak_idx + WINDOW_SIZE ]))

        aligned[i] = np.concatenate((aligned[i], traces_list[i + 1][peak_idx + WINDOW_SIZE:]))

    return aligned

def peak_disalignment(traces):
    diffs = []
    template = np.argmax(traces[0], axis=0)
    for i in range(1,len(traces)):
        diffs.append([])
        diffs[i - 1].append(np.argmax(traces[i][template - WINDOW_SIZE: template +WINDOW_SIZE],axis=0) - WINDOW_SIZE)
    return diffs


def plot(traces, copies):
    _, axs = plt.subplots(2)
    
    # Plot the first subplot
    for i in range(NUM_OF_TRACES):
        axs[0].plot(traces[i], label='Trace '+ str(i))
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


def create_trs():
    data = []

    with trsfile.trs_open(sys.argv[1], 'r', enigine='TrsEngine') as traces:
        with trsfile.trs_open(EXPORT_PATH, 'w', headers = {
            trsfile.Header.TRS_VERSION: 2,
            trsfile.Header.DESCRIPTION: "Copied",
            trsfile.Header.SCALE_X: traces.get_headers().get(trsfile.Header.SCALE_X),
            trsfile.Header.SCALE_Y: traces.get_headers().get(trsfile.Header.SCALE_Y),
            trsfile.Header.TRACE_PARAMETER_DEFINITIONS: TraceParameterDefinitionMap(
				{'LEGACY_DATA': tp.TraceParameterDefinition(tp.ParameterType.BYTE, 32, 0)})
            }, \
                padding_mode=trsfile.TracePadding.AUTO,live_update=True, engine='TrsEngine') as new_traces: 
            for i in trange(NUM_OF_TRACES):
                if i == 0:
                    data.append(np.array(traces[0].samples))
                else:
                    data.append(np.array(traces[i].samples))
                    aligned = align(np.array(data), peak_disalignment(np.array(data)))[0]
                # Adding one Trace
                new_traces.append(
                    trsfile.Trace(
                        trsfile.SampleCoding.FLOAT,
                        data[0] if i == 0 else aligned, 
                        TraceParameterMap({'LEGACY_DATA':
                            tp.ByteArrayParameter(bytes(traces[i].parameters['LEGACY_DATA'].value))}),
                    )
                )
                if (len(data) > 1):
                    data.pop()
def main():
    create_trs()

if __name__ == "__main__":
    main()
    run_correlation(EXPORT_PATH)

