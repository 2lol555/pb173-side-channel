import trsfile
from trsfile.parametermap import TraceSetParameterMap
import trsfile.traceparameter as tp
import matplotlib.pyplot as plt
import sys
import numpy as np

WINDOW_SIZE = 500
START = 25000
NUM_OF_TRACES = 3

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

def main(): 
    data = read_file() 
    diffs = peak_disalignment(data)
    aligned_traces = align(data, diffs)
    plot(data, aligned_traces)    

if __name__ == "__main__":
    main()
