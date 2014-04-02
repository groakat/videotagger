import numpy as np


def generateTrajFeatures(traj, dt=0.033):
    """ Calculate Trajectory Features as in Burgos-Artizzu CVPR 2012

    Args:
        traj (ndarray):
                            two dimensional matrix with x,y
                            positions for each time step t
        dt (float):
                            time difference between two positions
                            in traj

    Returns:
        feat (ndarray):
                            N x 7 matrix
    """

    # convenience functions to zero pad t offsets
    # t -1
    t_m1 = lambda x: np.pad(x[:-1], (1, 0), mode='constant')
    # t - 2
    t_m2 = lambda x: np.pad(x[:-2], (2, 0), mode='constant')
    # t + 1
    t_p1 = lambda x: np.pad(x[1:], (0, 1), mode='constant')

    # position
    position = traj

    # traj differences
    dx = traj[:, 0] - t_m1(traj[:, 0])
    dy = traj[:, 1] - t_m1(traj[:, 1])

    # direction
    # direction = dy / dx
    # direction[np.isnan(direction)] = 0
    direction = np.arctan2(dy, dx)

    dir_change = direction - t_m1(direction)

    # velocity
    vx = 1 / dt * (0.25 * t_m1(dx) + 0.5 * dx + 0.25 * t_p1(dx))
    vy = 1 / dt * (0.25 * t_m1(dy) + 0.5 * dy + 0.25 * t_p1(dy))

    # acceleration
    ax = (t_p1(vx) - t_m1(vx)) / (2 * dt)
    ay = (t_p1(vy) - t_m1(vy)) / (2 * dt)

    # concatenate feature vector/matrix
    # using np.c_ instead of np.concatenate to avoid problems with
    # shape of position and the other features
    feat = np.c_[position, direction, dir_change,
                           vx, vy, ax, ay]

    return feat