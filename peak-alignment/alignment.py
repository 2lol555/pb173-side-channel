import trsfile
from trsfile.parametermap import TraceSetParameterMap
import trsfile.traceparameter as tp
import matplotlib.pyplot as plt
import sys
import numpy as np

with trsfile.open("AES_fixed_rand_input_CAFEBABEDEADBEEF0001020304050607_SAVEEVEN_0_1000_.trs", 'r') as traces:
    for header, value in traces.get_headers().items():
        print(header, '=', value)
   
    print(traces[0].samples)
    print(type(traces[0].samples))
    print(len(traces[0].samples))
    diffs = []
    
    WINDOW_SIZE = 2000
    START = 25000
    
    template = np.argmax(traces[0].samples[START: WINDOW_SIZE + START ], axis=0)
    print(template + START)
    
    for i in range(1,3):
            diffs.append([])
            diffs[i - 1].append(np.argmax(traces[i].samples[ START: WINDOW_SIZE + START ], axis=0) - template)
    
    print(diffs)

    copies = [[] for _ in range(2)]

    for i in range(len(copies)):
        copies[i].extend(traces[i + 1].samples[:START])
        if (diffs[i][0] < 0):
            copies[i].extend([0 for _ in range(abs(diffs[i][0]))])
            copies[i].extend(traces[i + 1].samples[START: WINDOW_SIZE + START ])
        else:
             copies[i].extend(traces[i + 1].samples[ START + diffs[i][0]: WINDOW_SIZE + START ])

        copies[i].extend(traces[i + 1].samples[WINDOW_SIZE + START:])

    print(len(copies))
    print(len(copies[0]))
    print(len(copies[1]))

    fig, axs = plt.subplots(2)
    
    # Plot the first subplot
    axs[0].plot(traces[0].samples, label='Trace 1')
    axs[0].plot(traces[1].samples, label='Trace 2')
    axs[0].plot(traces[2].samples, label='Trace 3')
    axs[0].set_title('First Subplot')
    axs[0].legend()
    
    # Plot the second subplot
    axs[1].plot(traces[0].samples, label='Trace 1\'')
    axs[1].plot(copies[0], label='Trace 2\'')
    axs[1].plot(copies[1], label='Trace 3\'')
    axs[1].set_title('Second Subplot')
    axs[1].legend()
    
    plt.tight_layout()  # Adjust layout to prevent overlap
    plt.show()

