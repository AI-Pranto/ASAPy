import numpy as np
import SALib.sample.latin as lhs
from scipy.stats import multivariate_normal
from scipy.stats.distributions import norm

def correlation_to_cov(std, corr):
    """
    Calculates the cov matrix from correlation matrix + known std_devs
    Parameters
    ----------
    std : np.array
    corr : np.array

    Returns
    -------
    np.array
        The cov matrix

    """

    # given R_{ij} = \frac{C_{ij}}{\sqrt{C_{ii} C_{jj}}} and
    # knowing C_ii = (std_dev of variable i)**2 and C_jj = (std_dev of variable j)**2

    cov = np.diag(std**2)

    shape = len(std)
    for i in range(shape):
        for j in range(i+1, shape):
            cov[i, j] = corr[i, j] * std[i] * std[j] #(cov[i, i] * cov[j, j]) ** 0.5

    cov = cov + cov.T - np.diag(np.diag(cov))

    return cov

def cov_to_correlation(cov):

    shape = len(cov)
    corr = np.diag(np.ones(shape))
    for i in range(shape):
        for j in range(i+1, shape):
            corr[i, j] = cov[i, j] / np.abs(cov[i, i] * cov[j, j]) ** 0.5


    corr = corr + corr.T - np.diag(np.diag(corr))
    return corr

_FINFO = np.finfo(float)
_EPS = _FINFO.eps

def gmw_cholesky(A):
    """
    Provides a partial cholesky decomposition that is correct minus a matrix e

    Return `(P, L, e)` such that `P.T*A*P = L*L.T - diag(e)`.

    Returns
    -------
    P : 2d array
       Permutation matrix used for pivoting.
    L : 2d array
       Lower triangular factor
    e : 1d array
    Positive diagonals of shift matrix `e`.

    Notes
    -----
    The Gill, Murray, and Wright modified Cholesky algorithm.

    Algorithm 6.5 from page 148 of 'Numerical Optimization' by Jorge
    Nocedal and Stephen J. Wright, 1999, 2nd ed.

    This implimentation from https://bitbucket.org/mforbes/pymmf/src/c0028c213c8765e4aa62730e379731b89fcaebff/mmf/math/linalg/cholesky/gmw81.py?at=default

    """
    n = A.shape[0]

    # Test matrix.
    #A = array([[4, 2, 1], [2, 6, 3], [1, 3, -0.004]], Float64)
    #n = len(A)
    #I = identity(n, Float64)

    # Calculate gamma(A) and xi(A).
    gamma = 0.0
    xi = 0.0
    for i in range(n):
        gamma = max(abs(A[i, i]), gamma)
        for j in range(i+1, n):
            xi = max(abs(A[i, j]), xi)

    # Calculate delta and beta.
    delta = _EPS * max(gamma + xi, 1.0)
    if n == 1:
        beta = np.sqrt(max(gamma, _EPS))
    else:
        beta = np.sqrt(max(gamma, xi / np.sqrt(n**2 - 1.0), _EPS))

    # Initialise data structures.
    a = 1.0 * A
    r = 0.0 * A
    e = np.zeros(n, dtype=float)
    P = np.eye(n, dtype=float)

    # Main loop.
    for j in range(n):
        # Row and column swapping, find the index > j of the largest
        # diagonal element.
        q = j
        for i in range(j+1, n):
            if abs(a[i, i]) >= abs(a[q, q]):
                q = i

        # Interchange row and column j and q (if j != q).
        if q != j:
            # Temporary permutation matrix for swaping 2 rows or columns.
            p = np.eye(n, dtype=float)

            # Modify the permutation matrix P by swaping columns.
            row_P = 1.0*P[:, q]
            P[:, q] = P[:, j]
            P[:, j] = row_P

            # Modify the permutation matrix p by swaping rows (same as
            # columns because p = pT).
            row_p = 1.0*p[q]
            p[q] = p[j]
            p[j] = row_p

            # Permute a and r (p = pT).
            a = np.dot(p, np.dot(a, p))
            r = np.dot(r, p)

        # Calculate dj.
        theta_j = 0.0
        if j < n-1:
            for i in range(j+1, n):
                theta_j = max(theta_j, abs(a[j, i]))
        dj = max(abs(a[j, j]), (theta_j/beta)**2, delta)

        # Calculate e (not really needed!).
        e[j] = dj - a[j, j]

        # Calculate row j of r and update a.
        r[j, j] = np.sqrt(dj)     # Damned sqrt introduces roundoff error.
        for i in range(j+1, n):
            r[j, i] = a[j, i] / r[j, j]
            for k in range(j+1, i+1):
                a[i, k] = a[k, i] = a[k, i] - r[j, i] * r[j, k]     # Keep matrix a symmetric.

    # The Cholesky factor of A.
    return P, r.T, e


def lhs_uniform_sample(num_vars, num_samples):
    """
    Create uncorrelated uniform samples on the unit interval

    Parameters
    ----------
    num_vars
    num_samples

    Returns
    -------

    """
    samples = lhs.sample({'num_vars': num_vars, 'bounds': [[0, 1] for i in range(num_vars)]}, num_samples)

    return samples

def lhs_normal_sample(num_samples, means, std_dev):
    """
    Creates uncorrelated normally distributed sample with mean means and standard deviation std_dev

    Parameters
    ----------
    num_vars
    num_samples
    means
    std_dev

    Returns
    -------

    """
    num_vars = len(means)
    samples = lhs_uniform_sample(num_vars, num_samples)

    for i in range(num_vars):
        # create a norm distro with mean/std_dev then sample from it using percent point func (inv of cdf percentiles)
        samples[:, i] = norm(loc=means[i], scale=std_dev[i]).ppf(samples[:, i])

    return samples

def normal_sample_corr(mean_values, desired_cov, num_samples, allow_singular=False):
    """
    Randomally samples from a normal-multivariate distribution with mean mean_values and cov desired_cov

    Parameters
    ----------
    mean_values
    desired_cov
    num_samples

    Returns
    -------
    np.array

    """
    m = multivariate_normal(mean=mean_values, cov=desired_cov, allow_singular=allow_singular)
    return m.rvs(num_samples)

def lhs_normal_sample_corr(mean_values, std_dev, desired_corr, num_samples):
    """
    Randomally samples from a normal-multivariate distribution using LHS while attempting to get the desired_cov

    Parameters
    ----------
    mean_values
    desired_cov
    num_samples

    Returns
    -------

    """

    # draw samples in an uncorrelated manner
    num_vars = len(mean_values)
    samples = lhs_normal_sample(num_samples, np.zeros(num_vars), np.ones(num_vars))

    # cholesky-like decomp for non PD matricies.
    T = np.corrcoef(samples.T)
    permutation, Q, e = gmw_cholesky(T)

    # this matrix has the same correlation as the desired RStar
    P = np.linalg.cholesky(desired_corr)

    dependent_samples = np.dot(samples, np.dot(P, np.linalg.inv(Q)).T)

    # for il=1:ntry

    #     for j=1:nvar
    #         % rank RB
    #         [r,id]=ranking(RB(:,j));
    #         % sort R
    #         [RS,id]=sort(R(:,j));
    #         % permute RS so has the same rank as RB
    #         z(:,j) = RS(r).*xsd(j)+xmean(j);
    #     end
    #     ae=sum(sum(abs(corrcoef(z)-corr)));
    #     if(ae<amin)
    #         zb=z;
    #         amin=ae;
    #     end
    # end

    ntry = 1
    amin = 1.8e308
    z = np.zeros(np.shape(samples))
    for il in range(ntry):
        for j in range(num_vars):
            r = np.argsort(dependent_samples[:, j])
            rank = np.zeros(np.shape(r), dtype=int)
            rank[r] = np.array(range(num_samples))
            rs = np.sort(samples[:, j])
            z[:, j] = np.multiply(rs[rank], std_dev[j]) + mean_values[j]

        ae = np.abs(np.corrcoef(z.T) - desired_corr).sum().sum()

        if ae < amin:
            zb = z
            amin = ae
        else:
            raise Exception('Could not order samples ae={0}'.format(ae))

    # we could transform these back to uniform then transform to another distribution but want normal so we good

    return zb

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    desired_corr = np.diag([1]*25) + np.diag([-0.5]*24, 1) + np.diag([-0.5]*24, -1)

    dependent_samples = lhs_normal_sample_corr(np.array(np.ones(25)*20), np.ones(25)*0.05*20, desired_corr, 500)

    fig, ax = plt.subplots()

    ax.plot(dependent_samples[4, :])
    plt.show()

    # correlation is good..
    plt.imshow(np.corrcoef(dependent_samples.T))
    plt.colorbar()
    plt.show()