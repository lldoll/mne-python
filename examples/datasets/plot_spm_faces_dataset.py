"""
==========================================
From raw data to dSPM on SPM Faces dataset
==========================================

Runs a full pipeline using MNE-Python:
- averaging Epochs
- forward model computation
- source reconstruction using dSPM on the contrast : "faces - scrambled"

"""
print __doc__

# Authors: Alexandre Gramfort <alexandre.gramfort@telecom-paristech.fr>
#          Denis Engemann <d.engemann@fz-juelich.de>
#
# License: BSD (3-clause)

import matplotlib.pyplot as plt

import mne
from mne.datasets import spm_face
from mne import fiff
from mne.minimum_norm import make_inverse_operator, apply_inverse

data_path = spm_face.data_path()
subjects_dir = data_path + '/subjects'

###############################################################################
# Set parameters
raw_fname = data_path + '/MEG/spm/SPM_CTF_MEG_example_faces%d_3D_raw.fif'

# Or just one:
raw = fiff.Raw(raw_fname % 1, preload=True)

raw.filter(1, 45, method='iir')

events = mne.find_events(raw, stim_channel='UPPT001')

event_ids = {"faces":1, "scrambled":2}

tmin, tmax = -0.2, 0.6
baseline = None  # no baseline as high-pass is applied

reject = dict(mag=1.5e-12)

epochs = mne.Epochs(raw, events, event_ids, tmin, tmax, proj=True,
                    baseline=baseline, preload=True, reject=reject)
evoked = [epochs[k].average() for k in event_ids]
noise_cov = mne.compute_covariance(epochs.crop(None, 0))

constrast = evoked[1] - evoked[0]

evoked.append(constrast)

plt.close('all')
for e in evoked:
    plt.figure()
    e.plot(ylim=dict(mag=[-400, 400]))

plt.show()

###############################################################################
# Compute forward model

# Make source space
src = mne.setup_source_space('spm', spacing='oct6', subjects_dir=subjects_dir)

mri = data_path + '/MEG/spm/SPM_CTF_MEG_example_faces1_3D_raw-trans.fif'
bem = data_path + '/subjects/spm/bem/spm-5120-5120-5120-bem-sol.fif'
forward = mne.make_forward_solution(raw.info, mri=mri, src=src, bem=bem)
forward = mne.convert_forward_solution(forward, surf_ori=True)

###############################################################################
# Compute inverse solution

snr = 3.0
lambda2 = 1.0 / snr ** 2
method = 'dSPM'

inverse_operator = make_inverse_operator(epochs.info, forward, noise_cov,
                                         loose=0.2, depth=0.8)

# Compute inverse solution on contrast
stc = apply_inverse(constrast, inverse_operator, lambda2, method,
                    pick_normal=False)
# stc.save('spm_%s_dSPM_inverse' % constrast.comment)

# plot constrast
# Plot brain in 3D with PySurfer if available. Note that the subject name
# is already known by the SourceEstimate stc object.
brain = stc.plot(surface='inflated', hemi='both', subjects_dir=subjects_dir)
brain.set_data_time_index(173)
brain.scale_data_colormap(fmin=2, fmid=4, fmax=6, transparent=True)
brain.show_view('ventral')
# brain.save_image('dSPM_map.png')
