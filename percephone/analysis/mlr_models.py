"""
Théo Gauvrit 18/01/2024
Multiple Linear regression analysis
"""

import matplotlib
import numpy as np
from percephone.analysis.utils import kernel_biexp
import matplotlib.pyplot as plt
matplotlib.use("Qt5Agg")
plt.switch_backend("Qt5Agg")


def regressor_labels(rec, timings, duration, len_signal, amplitude=100):
    """
    Convolve label events to obtain regressor for Multiple Linear Regression
    Parameters
    ----------
    rec: RecordingAmplDet
        recording considered
    timings: array
        timings in index of the label events
    duration: array
        duration of the label events
    amplitude: int
        amplitude of the label events
    len_signal: int
        length of the df/f trace in index

    Returns
    -------
    regressor: array
        convolved behavior label events
    """
    vector = np.zeros(len_signal)
    index = [list(range(stim, int(stim + duration[i]))) for i, stim in enumerate(timings)]
    index = np.concatenate(index)
    vector[index[index < len(vector)]] = amplitude
    regressor = np.convolve(vector, kernel_biexp(rec.sf), mode='same') * (1 / rec.sf)
    return regressor


def classic_model(rec):
    timings = rec.stim_time[rec.detected_stim]
    duration = rec.stim_durations[rec.detected_stim]
    conv_stim_det = regressor_labels(rec, timings, duration, len(rec.zscore_exc[0]), 100)
    undet_timings = rec.stim_time[~rec.detected_stim]
    undet_duration = rec.stim_durations[~rec.detected_stim]
    conv_stim_undet = regressor_labels(rec,  undet_timings, undet_duration, len(rec.zscore_exc[0]), 100)
    reward_duration = np.array([int(0.1 * rec.sf)]*len(rec.reward_time))  # 0.1 s
    conv_reward = regressor_labels(rec, rec.reward_time, reward_duration, len(rec.zscore_exc[0]), 200)
    timeout_duration = np.array([int(2 * rec.sf)]*len(rec.timeout_time))  # 2 s
    conv_timeout = regressor_labels(rec, rec.timeout_time, timeout_duration, len(rec.zscore_exc[0]), 100)
    return np.array([conv_stim_det, conv_stim_undet, conv_reward, conv_timeout]), "classic_model"


def r2_model(rec):
    """Most simple model. Two regressors model stim detected and reward."""
    timings = rec.stim_time[rec.detected_stim]
    duration = rec.stim_durations[rec.detected_stim]
    conv_stim_det = regressor_labels(rec, timings, duration, len(rec.zscore_exc[0]), 100)
    reward_duration = np.array([int(0.1 * rec.sf)] * len(rec.reward_time))  # 0.1 s
    conv_reward = regressor_labels(rec, rec.reward_time, reward_duration, len(rec.zscore_exc[0]), 200)
    return np.array([conv_stim_det,  conv_reward]), "r2_model"


def stim_ud_model(rec):
    """Most simple model. Two regressors model stim detected and reward."""
    timings = rec.stim_time[rec.detected_stim]
    duration = rec.stim_durations[rec.detected_stim]
    conv_stim_det = regressor_labels(rec, timings, duration, len(rec.zscore_exc[0]), 100)
    undet_timings = rec.stim_time[~rec.detected_stim]
    undet_duration = rec.stim_durations[~rec.detected_stim]
    conv_stim_undet = regressor_labels(rec, undet_timings, undet_duration, len(rec.zscore_exc[0]), 100)
    return np.array([conv_stim_det,  conv_stim_undet])


def precise_stim_model(rec):
    """Variation of the classic model where all the stims are stopped with the first lick. So
    the stim regressors is shorter"""
    timings = rec.stim_time[rec.detected_stim]
    duration = [np.min(np.array(rec.lick_time-timing)[(rec.lick_time - timing)>0]) for timing in timings]
    conv_stim_det = regressor_labels(rec, timings, duration, len(rec.zscore_exc[0]), 100)
    undet_timings = rec.stim_time[~rec.detected_stim]
    undet_duration = rec.stim_durations[~rec.detected_stim]
    conv_stim_undet = regressor_labels(rec,  undet_timings, undet_duration, len(rec.zscore_exc[0]), 100)
    lick_duration = np.array([int(0.1 * rec.sf)]*len(rec.lick_time))  # 0.1 s
    conv_lick = regressor_labels(rec, rec.lick_time, lick_duration, len(rec.zscore_exc[0]), 200)
    return np.array([conv_stim_det, conv_stim_undet, conv_lick]), "precise_stim_model"


def biphase_stim_model(rec):
    """The stim are split into two phases: start 02s and end 0.3s. The lick are split into as well
    between lick reward and other licks"""
    amp = 10
    timings = rec.stim_time[rec.detected_stim]
    p1_t = timings
    p2_t = timings + 15
    p1_dur = np.array([int(0.2 * rec.sf)]*len(timings))
    p2_dur = np.array([int(0.3 * rec.sf)]*len(timings))
    conv_stim_p1 = regressor_labels(rec, p1_t, p1_dur, len(rec.zscore_exc[0]), amp)
    conv_stim_p2 = regressor_labels(rec, p2_t, p2_dur, len(rec.zscore_exc[0]), amp)
    undet_timings = rec.stim_time[~rec.detected_stim]
    up1_t = undet_timings
    up2_t = undet_timings + 15
    up1_dur = np.array([int(0.2 * rec.sf)] * len(undet_timings))
    up2_dur = np.array([int(0.3 * rec.sf)] * len(undet_timings))
    uconv_stim_p1 = regressor_labels(rec,  up1_t, up1_dur, len(rec.zscore_exc[0]), amp)
    uconv_stim_p2 = regressor_labels(rec, up2_t, up2_dur, len(rec.zscore_exc[0]), amp)
    reward_duration = np.array([int(0.1 * rec.sf)] * len(rec.reward_time))  # 0.1 s
    conv_reward = regressor_labels(rec, rec.reward_time, reward_duration, len(rec.zscore_exc[0]), amp)
    lick_duration = np.array([int(0.1 * rec.sf)]*len(rec.lick_time))  # 0.1 s
    conv_lick = regressor_labels(rec, set(rec.lick_time).difference(set(rec.reward_time)), lick_duration,
                                 len(rec.zscore_exc[0]), amp)
    return (np.array([conv_stim_p1, conv_stim_p2, uconv_stim_p1, uconv_stim_p2, conv_reward, conv_lick]),
            "biphase_stim_model")


# def bi_stim_model(rec):
#     """Two regressors: one for the begining of the stim and the second for the end of the stim"""
#     timings = rec.stim_time[rec.detected_stim]
#     start_duration = rec.stim_durations[rec.detected_stim]/2
#     start_stim = regressor_labels(rec, timings, duration, len(rec.zscore_exc[0]), 100)
#     end_duration = rec.stim_durations[rec.detected_stim]/2  # 0.1 s
#     end_stim = regressor_labels(rec, rec.reward_time, reward_duration, len(rec.zscore_exc[0]), 200)
#     return np.array([start_stim,  end_stim])
