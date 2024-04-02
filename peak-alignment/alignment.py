import trsfile
from trsfile.parametermap import TraceSetParameterMap, TraceParameterMap, TraceParameterDefinitionMap
import trsfile.traceparameter as tp
import matplotlib.pyplot as plt
import sys
import numpy as np
import os
from correlation import run_correlation

WINDOW_SIZE = 500
START = 25000
NUM_OF_TRACES = 3
EXPORT_PATH = 'trace-set.trs'


def read_file():
    samples_list = []
    with trsfile.open(sys.argv[1], 'r') as traces:
        for header, value in traces.get_headers().items():
            print(header, '=', value)
        for i in range(NUM_OF_TRACES):
            samples_list.append(traces[i].samples)
    return samples_list


def align(traces_list, diffs):
    aligned = [[] for _ in range(len(traces_list) - 1)]
    for i in range(len(traces_list) - 1):
        peak_idx = np.argmax(traces_list[i + 1], axis=0);
        average = np.mean(traces_list[i + 1], axis=0);
        aligned[i].extend(traces_list[i + 1][:peak_idx - WINDOW_SIZE])
        if (diffs[i][0] < 0):
            aligned[i].extend([average for _ in range(abs(diffs[i][0]))])
            aligned[i].extend(traces_list[i + 1][peak_idx - WINDOW_SIZE: peak_idx + WINDOW_SIZE])
        else:
            aligned[i].extend(traces_list[i + 1][ peak_idx - WINDOW_SIZE + diffs[i][0]: peak_idx + WINDOW_SIZE ])

        aligned[i].extend(traces_list[i + 1][peak_idx + WINDOW_SIZE:])
    
    return aligned


def peak_disalignment(traces):
    diffs = []
    template = np.argmax(traces[0], axis=0)
    for i in range(1,NUM_OF_TRACES):
        diffs.append([])
        diffs[i - 1].append(np.argmax(traces[i][template - WINDOW_SIZE: template +WINDOW_SIZE],axis=0) - WINDOW_SIZE)
    print(diffs)
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


def create_trs(data, aligned_traces):
    #TODO: copy header from original trs file
    with trsfile.trs_open(
            EXPORT_PATH,                 # File name of the trace set
		'w',                             # Mode: r, w, x, a (default to x)
		# Zero or more options can be passed (supported options depend on the storage engine)
		engine = 'TrsEngine',            # Optional: how the trace set is stored (defaults to TrsEngine)
		headers = {                      # Optional: headers (see Header class)
			trsfile.Header.TRS_VERSION: 2,
			trsfile.Header.SCALE_X: 1e-6,
			trsfile.Header.SCALE_Y: 0.1,
			trsfile.Header.DESCRIPTION: 'Aligned Peak',
			trsfile.Header.TRACE_PARAMETER_DEFINITIONS: TraceParameterDefinitionMap(
				{'LEGACY_DATA': tp.TraceParameterDefinition(tp.ParameterType.BYTE, 16, 0)})
		},
		padding_mode = trsfile.TracePadding.AUTO,# Optional: padding mode (defaults to TracePadding.AUTO)
		live_update = True               # Optional: updates the TRS file for live preview (small performance hit)
		                                 #   0 (False): Disabled (default)
		                                 #   1 (True) : TRS file updated after every trace
		                                 #   N        : TRS file is updated after N traces
	) as traces:

        peak_idx = np.argmax(data[0], axis=0);
        #TODO: copy legacy data from original traces
        traces.append(
                trsfile.Trace(
                    trsfile.SampleCoding.FLOAT,
                    data[0][ peak_idx - WINDOW_SIZE: peak_idx + WINDOW_SIZE ],
                    TraceParameterMap({'LEGACY_DATA': tp.ByteArrayParameter(os.urandom(16))})
                )
        )
        for i in range(0, len(aligned_traces)):
            peak_idx = np.argmax(aligned_traces[i], axis=0)
            # Adding one Trace
            traces.append(
                trsfile.Trace(
                    trsfile.SampleCoding.FLOAT,
                    aligned_traces[i][ peak_idx - WINDOW_SIZE: peak_idx + WINDOW_SIZE ],
                    TraceParameterMap({'LEGACY_DATA': tp.ByteArrayParameter(os.urandom(16))})
                )
            )

def main(): 
    data = read_file() 
    diffs = peak_disalignment(data)
    aligned_traces = align(data, diffs)
    create_trs(data, aligned_traces)
    plot(data, aligned_traces)    

if __name__ == "__main__":
    main()
    run_correlation(EXPORT_PATH)