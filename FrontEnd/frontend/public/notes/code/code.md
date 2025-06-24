# CUDA Kernels for Autocorrelation and Reduction

This package provides high-performance CUDA implementations of autocorrelation and sum reduction operations, designed to accelerate scientific computing tasks.

## Installation

```bash
pip install cuda-kernels
```

## Usage Examples

### Autocorrelation Example

```python
import numpy as np
from cuda_kernels.autocorrelation import autocorrelation

# Create or load your time series data
data = np.random.randn(10000).astype(np.float32)

# Calculate autocorrelation for lags 0-100
result = autocorrelation(data, max_lag=100)

# Plot the results
import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
plt.plot(result)
plt.title('Autocorrelation')
plt.xlabel('Lag')
plt.ylabel('Correlation')
plt.grid(True)
plt.show()
```

### Sum Reduction Example

```python
import numpy as np
from cuda_kernels.reduction import reduction_sum

# Create a large array
data = np.random.randn(1000000).astype(np.float32)

# Calculate sum using GPU
gpu_sum = reduction_sum(data)
print(f"GPU Sum: {gpu_sum}")

# Verify with NumPy
numpy_sum = np.sum(data)
print(f"NumPy Sum: {numpy_sum}")
```

## Source Code

### Autocorrelation Kernel

```c
__global__ void gpu_autocorrelation(const float* __restrict__ data, float* __restrict__ result, int size, int max_lag) {
    extern __shared__ float shared_sum[];
    int lag = blockIdx.x;
    if (lag >= max_lag) return;

    int tid = threadIdx.x;
    int block_size = blockDim.x;
    float sum = 0.0f;

    for (int i = tid; i < size - lag; i += block_size) {
        sum += data[i] * data[i + lag];
    }

    shared_sum[tid] = sum;
    __syncthreads();

    for (int s = block_size / 2; s > 32; s >>= 1) {
        if (tid < s) {
            shared_sum[tid] += shared_sum[tid + s];
        }
        __syncthreads();
    }

    if (tid < 32) {
        volatile float* vshared = shared_sum;
        vshared[tid] += vshared[tid + 32];
        vshared[tid] += vshared[tid + 16];
        vshared[tid] += vshared[tid + 8];
        vshared[tid] += vshared[tid + 4];
        vshared[tid] += vshared[tid + 2];
        vshared[tid] += vshared[tid + 1];
    }

    if (tid == 0) {
        result[lag] = shared_sum[0];
    }
}
```

### Sum Reduction Kernel

```c
__global__ void gpu_reduction_sum_kernel(float* d_in, int size, float* d_out) {
    extern __shared__ float sdata[];
    unsigned int tid = threadIdx.x;
    unsigned int idx = blockIdx.x * blockDim.x * 2 + threadIdx.x;
    float sum = 0.0f;
    if (idx < size) {
        sum = d_in[idx];
        if (idx + blockDim.x < size)
            sum += d_in[idx + blockDim.x];
    }
    sdata[tid] = sum;
    __syncthreads();

    for (unsigned int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (tid < s) {
            sdata[tid] += sdata[tid + s];
        }
        __syncthreads();
    }
    if (tid == 0)
        d_out[blockIdx.x] = sdata[0];
}
```

## Performance

These CUDA implementations can provide significant speedups compared to CPU-based implementations:

- Autocorrelation: 10-100x speedup for large time series
- Sum Reduction: 5-50x speedup for large arrays

## Requirements

- NVIDIA GPU with CUDA support
- CUDA Toolkit (version 11.0+ recommended)
- Python 3.6+
- NumPy

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.