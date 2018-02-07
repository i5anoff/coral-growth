# cython: boundscheck=False
# cython: wraparound=False
# cython: initializedcheck=False
# cython: nonecheck=False
# cython: cdivision=True
from __future__ import division, print_function
import numpy as np
cimport numpy as np
from random import shuffle
from libc.math cimport floor, fmin, fmax, fabs, atan, acos, cos, sin
from cymesh.vector3D cimport inormalized, vadd, vsub, vmultf, vset, dot

cdef double[:,:] spreads = np.array([
    [1, 0, 0, 0],
    [0.24522841, 0.12498851, 0, 0],
    [0.08729082, 0.06935493, 0.03472476, 0],
    [0.04280001, 0.03837332, 0.02765348, 0.01601401],
])

cpdef void createPolypInputs(object coral) except *:
    """ Map polyp stats to nerual input in [-1, 1] range. """
    cdef int input_idx, i, mi, mbin
    cdef int n_morphogens = coral.morphogens.n_morphogens
    cdef int morphogen_thresholds = coral.morphogen_thresholds
    cdef double[:,:] morphogensU = coral.morphogens.U
    cdef double[:] polyp_light = coral.polyp_light
    cdef double[:,:] polyp_normal = coral.polyp_normal
    cdef double[:] polyp_gravity = coral.polyp_gravity
    cdef double[:] polyp_collection = coral.polyp_collection
    cdef double[:,:] polyp_signals = coral.polyp_signals
    cdef double[:,:] inputs = coral.polyp_inputs
    cdef bint use_polar_direction = coral.params.use_polar_direction
    cdef int num_inputs = coral.num_inputs
    cdef list neighbors
    cdef double signal_sum, azimuthal_angle, polar_angle

    inputs[:, :] = -1

    for i in range(coral.n_polyps):
        inputs[i, 0] = (polyp_light[i] * 2) - 1
        inputs[i, 1] = (polyp_collection[i] * 2) - 1

        input_idx = 2

        # Morphogens
        for mi in range(n_morphogens):
            mbin = <int>(floor(morphogensU[mi, i] * morphogen_thresholds))
            mbin = min(morphogen_thresholds - 1, mbin)

            if mbin > 0:
                inputs[i, input_idx + (mbin-1)] = 1

            input_idx += (morphogen_thresholds-1)

        # Signals
        for mi in range(coral.n_signals):
            inputs[i, input_idx] = polyp_signals[i, mi] > 0.5
            input_idx += 1

        if use_polar_direction:
            azimuthal_angle = atan(polyp_normal[i, 1] / polyp_normal[i, 0])
            polar_angle = acos(polyp_normal[i, 2])
            inputs[i, input_idx] = cos(azimuthal_angle)
            inputs[i, input_idx+1] = sin(azimuthal_angle)
            inputs[i, input_idx+2] = cos(polar_angle)
            inputs[i, input_idx+3] = sin(polar_angle)
            input_idx += 4

        inputs[i, input_idx] = 1 # Bias Bit

        assert input_idx == (num_inputs-1)

cpdef void grow_polyps(object coral) except *:
    cdef int i, out_idx, sr
    cdef unsigned int mi
    cdef int n_memory = coral.n_memory
    cdef int n_signals = coral.n_signals
    cdef int n_morphogens = coral.n_morphogens
    cdef list neighbors
    cdef object output
    cdef double[:,:] polyp_pos = coral.polyp_pos
    cdef double[:,:] polyp_normal = coral.polyp_normal
    cdef double[:,:] pos_next = coral.polyp_pos_next
    cdef double[:,:] morphogensV = coral.morphogens.V
    cdef double[:] signal_decay = coral.signal_decay
    cdef int[:] signal_range = coral.signal_range
    cdef double[:] growth = np.zeros(coral.n_polyps)
    cdef double target_edge_len = coral.target_edge_len
    cdef double[:,:] polyp_signals = coral.polyp_signals

    cdef unsigned int net_depth = coral.net_depth
    cdef double max_growth = coral.max_growth
    cdef double growth_scalar, g
    cdef double total_growth = 0

    cdef double[:,:] polyp_pos_past = coral.polyp_pos_past

    polyp_pos_past[:coral.n_polyps,:] = polyp_pos[:coral.n_polyps, :]

    createPolypInputs(coral)

    cdef double old_volume = coral.mesh.volume()

    for i in range(coral.n_polyps):
        # Compute feed-forward network results.
        coral.network.Flush()
        coral.network.Input(coral.polyp_inputs[i])
        for _ in range(net_depth):
            coral.network.ActivateFast()
        output = coral.network.Output()

        # Move in normal direction by growth amount.
        growth[i] = output[0]
        polyp_pos[i, 0] += growth[i] * polyp_normal[i, 0]
        polyp_pos[i, 1] += growth[i] * polyp_normal[i, 1]
        polyp_pos[i, 2] += growth[i] * polyp_normal[i, 2]

        # Morphogens.
        out_idx = 1
        for mi in range(n_morphogens):
            if output[out_idx] > 0.5:
                morphogensV[mi, i] = 1.0
            out_idx += 1

        # Signals
        for mi in range(n_signals):
            sr = signal_range[mi]
            polyp_signals[i, mi] += spreads[sr, 0]

            if sr == 1:
                for vert in coral.polyp_verts[i].neighbors():
                    polyp_signals[vert.id, mi] += spreads[sr, 1] * output[out_idx]
            elif sr != 0:
                for d, vert in coral.mesh.getRings(coral.polyp_verts[i], sr):
                    polyp_signals[vert.id, mi] += spreads[sr, d+1] * output[out_idx]
            out_idx += 1

    cdef double new_volume = coral.mesh.volume()
    coral.mesh.calculateDefect()

    polyp_pos[:coral.n_polyps, :] = polyp_pos_past[:coral.n_polyps,:]

    # growth_scalar = coral.C
    total_growth = new_volume - old_volume
    if total_growth == 0:
        growth_scalar = 0.0
    else:
        growth_scalar = coral.C * coral.energy / total_growth

    for i in range(coral.n_polyps):
        g = min(growth[i] * growth_scalar, max_growth)

        pos_next[i, 0] = polyp_pos[i, 0] + g * polyp_normal[i, 0]
        pos_next[i, 1] = polyp_pos[i, 1] + g * polyp_normal[i, 1]
        pos_next[i, 2] = polyp_pos[i, 2] + g * polyp_normal[i, 2]
