from __future__ import print_function
import numpy as np
import mdtraj as md
from mdtraj.testing import get_fn, eq
from mdtraj.geometry import drid
from scipy.spatial.distance import euclidean, pdist, squareform


def test_drid_1():
    n_frames = 1
    n_atoms = 20
    top = md.Topology()
    chain = top.add_chain()
    residue = top.add_residue('X', chain)
    for i in range(n_atoms):
        top.add_atom('X', None, residue)
    
    t = md.Trajectory(xyz=np.random.RandomState(0).randn(n_frames, n_atoms, 3),
                      topology=top)
    # t contains no bonds
    got = drid.drid(t).reshape(n_frames, n_atoms, 3)

    for i in range(n_atoms):
        others = set(range(n_atoms)) - set([i])
        rd = 1 / np.array([euclidean(t.xyz[0, i], t.xyz[0, e]) for e in others])
        
        mean = np.mean(rd)
        second = np.mean((rd - mean)**2)**(0.5)
        third =  np.mean((rd - mean)**3)**(1.0 / 3.0)

        ref = np.array([mean, second, third])
        np.testing.assert_array_almost_equal(got[0, i], ref, decimal=5)


def test_drid_2():
    n_frames = 3    
    n_atoms = 11
    n_bonds = 5
    top = md.Topology()
    chain = top.add_chain()
    residue = top.add_residue('X', chain)
    for i in range(n_atoms):
        top.add_atom('X', None, residue)

    random = np.random.RandomState(0)
    bonds = random.randint(n_atoms, size=(n_bonds, 2))
    for a, b in bonds:
        top.add_bond(top.atom(a), top.atom(b))

    t = md.Trajectory(xyz=random.randn(n_frames, n_atoms, 3), topology=top)
    got = drid.drid(t).reshape(n_frames, n_atoms, 3)

    for i in range(n_frames):
        recip = 1 / squareform(pdist(t.xyz[i]))
        recip[np.diag_indices(n=recip.shape[0])] = np.nan
        recip[bonds[:, 0], bonds[:, 1]] = np.nan
        recip[bonds[:, 1], bonds[:, 0]] = np.nan

        mean = np.nanmean(recip, axis=0)
        second = np.nanmean((recip - mean)**2, axis=0)**(0.5)
        third =  np.nanmean((recip - mean)**3, axis=0)**(1.0 / 3.0)
        
        np.testing.assert_array_almost_equal(got[i, :, 0], mean, decimal=5)
        np.testing.assert_array_almost_equal(got[i, :, 1], second, decimal=5)
        
        # cbrt() in C handles negative numbers, but pow (above) doesn't. so
        # if the c code returns a negative third moment, the numpy code will
        # give nan
        np.testing.assert_array_almost_equal(np.maximum(got[i, :, 2], 0), np.nan_to_num(third), decimal=5)
