// fma_dequant_kernel.metal
// Illustrative Metal compute shader showing the FMA-optimized 4-bit dequantization.
// This demonstrates the algebraic trick at the core of Flash-MoE's 12% GPU speedup.
//
// From the article: https://aistackinsights.ai/blog/how-flash-moe-runs-397b-model-on-macbook
//
// Key insight: rearrange (nibble * scale + bias) * x
//           into fma(nibble, scale * x, bias * x)
// Pre-computing scale*x and bias*x per input vector lets the GPU FMA unit
// do dequantization + multiplication in a single instruction.

#include <metal_stdlib>
using namespace metal;

// Configuration — match to your model's expert dimensions
constant uint INPUT_DIM = 1024;  // Qwen3.5 expert intermediate dimension

kernel void matvec_4bit_fma(
    device const uchar* weights   [[ buffer(0) ]],  // packed 4-bit weights (2 per byte)
    device const float* input     [[ buffer(1) ]],  // input activation vector
    device float*       output    [[ buffer(2) ]],  // output vector
    device const float* scales    [[ buffer(3) ]],  // per-row quantization scales
    device const float* biases    [[ buffer(4) ]],  // per-row quantization biases (zero-points)
    uint   tid                    [[ thread_position_in_grid ]],
    uint   simd_lid               [[ thread_index_in_simdgroup ]]
) {
    // Each thread computes one output element (one row of the weight matrix)
    float acc = 0.0f;

    // Load scale and bias once per row — stays in registers
    float scale = scales[tid];
    float bias  = biases[tid];

    // Process two packed 4-bit weights per loop iteration
    for (uint i = 0; i < INPUT_DIM / 2; i++) {
        uchar packed = weights[tid * (INPUT_DIM / 2) + i];

        // Unpack two 4-bit nibbles
        float w0 = float(packed & 0x0F);   // low nibble
        float w1 = float(packed >> 4);      // high nibble

        float x0 = input[i * 2 + 0];
        float x1 = input[i * 2 + 1];

        // FMA trick: pre-compute scale*x and bias*x
        // GPU FMA unit: fma(a, b, c) = a*b + c in ONE instruction
        // Naive would be: (w0 * scale + bias) * x0  →  3 ops
        // FMA version:    fma(w0, scale * x0, bias * x0)  →  1 FMA + 2 muls (pre-computed)
        float sx0 = scale * x0;
        float bx0 = bias  * x0;
        float sx1 = scale * x1;
        float bx1 = bias  * x1;

        acc += fma(w0, sx0, bx0);
        acc += fma(w1, sx1, bx1);
    }

    // Reduce across SIMD group (32 threads) for tiled computation
    acc = simd_sum(acc);

    // Only lane 0 writes the final result
    if (simd_lid == 0) {
        output[tid] = acc;
    }
}
