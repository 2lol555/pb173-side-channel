import trsfile
from trsfile.parametermap import TraceSetParameterMap
from trsfile.parametermap import TraceParameterMap, TraceParameterDefinitionMap
from trsfile.traceparameter import ByteArrayParameter, ParameterType, TraceParameterDefinition
import matplotlib.pyplot as plt
import numpy as np
import os

s_box = None
parameters = None
value = None


def mean(x):
    return np.sum(x, axis=0) / len(x)


def std_dev(x, x_bar):
    return np.sqrt(np.sum((x - x_bar) ** 2, axis=0))


def cov(x, x_bar, y, y_bar):
    return np.sum((x - x_bar) * (y - y_bar), axis=0)


def aes_internal(input_data, key):
    return s_box[input_data ^ key]


def run_correlation(filepath):
    global s_box, parameters, value
    s_box = [
        # 0     1     2     3     4     5     6     7     8     9     a     b     c     d     e     f
        0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,  # 0
        0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,  # 1
        0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,  # 2
        0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,  # 3
        0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,  # 4
        0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,  # 5
        0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,  # 6
        0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,  # 7
        0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,  # 8
        0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,  # 9
        0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,  # a
        0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,  # b
        0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,  # c
        0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,  # d
        0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,  # e
        0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16  # f
    ]
    HW = [bin(n).count("1") for n in range(0, 256)]
    parameters = TraceSetParameterMap()
    print(parameters)
    zoomS = 0
    zoomE = 220000
    start = 0
    number = 1000
    displayLabels = 4
    dataS = 0
    dataN = 1
    useHW = False
    keyByte = 0xCA
    useIntermediate = True
    data = np.zeros((dataN - dataS, number), int)
    trace_array = np.zeros((number, zoomE - zoomS), float)

    with trsfile.open(filepath, 'r') as traces:
        print(traces.get_headers())
        # Show all headers
        for header, value in traces.get_headers().items():
            print(header, '=', value)
        scale_X = traces.get_headers().get(trsfile.Header.SCALE_X)

        for i, trace in enumerate(traces[start:start + number]):
            trace_array[i] = trace.samples[zoomS:zoomE]
            for j in range(dataS, dataN):
                if useIntermediate:
                    if useHW:
                        data[j - dataS][i] = aes_internal(trace.parameters['LEGACY_DATA'].value[j], keyByte)
                    else:
                        data[j - dataS][i] = HW[aes_internal(trace.parameters['LEGACY_DATA'].value[j], keyByte)]
                else:
                    if useHW:
                        data[j - dataS][i] = HW[trace.parameters['LEGACY_DATA'].value[j]]
                    else:
                        data[j - dataS][i] = trace.parameters['LEGACY_DATA'].value[j]
    print("trace_array")
    print(trace_array)
    print(trace_array.shape)
    print("data")
    print(data)
    print(data.shape)
    with trsfile.trs_open(
            filepath[0:-4] + '+CORR-INTERMEDIATE.trs',  # File name of the trace set
            'w',  # Mode: r, w, x, a (default to x)
            # Zero or more options can be passed (supported options depend on the storage engine)
            engine='TrsEngine',  # Optional: how the trace set is stored (defaults to TrsEngine)
            headers={  # Optional: headers (see Header class)
                trsfile.Header.TRS_VERSION: 1,
                trsfile.Header.SCALE_X: scale_X,
                trsfile.Header.SCALE_Y: 1,
                trsfile.Header.DESCRIPTION: 'Correlation Traces',
                trsfile.Header.TRACE_PARAMETER_DEFINITIONS: TraceParameterDefinitionMap(
                    {'LEGACY_DATA': TraceParameterDefinition(ParameterType.BYTE, 32, 0)})
            },
            padding_mode=trsfile.TracePadding.AUTO,  # Optional: padding mode (defaults to TracePadding.AUTO)
            live_update=True  # Optional: updates the TRS file for live preview (small performance hit)
            #   0 (False): Disabled (default)
            #   1 (True) : TRS file updated after every trace
            #   N        : TRS file is updated after N traces
    ) as c_traces:
        t_bar = mean(trace_array)
        o_t = std_dev(trace_array, t_bar)

        for j in range(dataS, dataN):
            intermediate = np.array([data[j - dataS]]).transpose()

            d_bar = mean(intermediate)
            o_d = std_dev(intermediate, d_bar)
            covariance = cov(trace_array, t_bar, intermediate, d_bar)
            correlation = covariance / (o_t * o_d)

            if j < displayLabels:
                plt.plot(correlation, label="Inp[" + str(j) + "]")
            elif j == displayLabels:
                plt.plot(correlation, label="...")
            else:
                plt.plot(correlation)

            # Adding one Trace
            c_traces.append(
                trsfile.Trace(
                    trsfile.SampleCoding.FLOAT,
                    correlation,
                    TraceParameterMap({'LEGACY_DATA': ByteArrayParameter(os.urandom(32))})
                )
            )
    plt.xlabel("Time")
    plt.ylabel("Correlation Intermediates")
    plt.title("Correlation of indexes: [" + str(dataS) + "-" + str(dataS + dataN - 1) + "]")
    plt.legend()
    plt.show()
