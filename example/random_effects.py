#! /usr/bin/env python3
'''
{begin_markdown random_effect_xam}
{spell_markdown
    params
    covs
    param
    inv
    init
    finfo
    py
    ftol
    gtol
    gprior
    disp
    maxiter
    expit
}

# Getting Started Using CurveFit

## Generalized Logistic Model
The model for the mean of the data for this example is one of the following:
\[
    f(t; \alpha, \beta, p)  = \frac{p}{1 + \exp [ -\alpha(t  - \beta) ]}
\]
where \( \alpha \), \( \beta \), and \( p \) are unknown parameters.


## Fixed and Random Effects
We use the notation \( a_j \), \( b_j \) and \( \phi_j \) for
the fixed effects, \( j = 0 \),
and the random effects \( j = 1 , \ldots , n_G \).
For this example, the link functions, that maps from the fixed and random
effects to the parameters, are
\[
\begin{aligned}
\begin{aligned}
    \alpha_j & = \exp \left( a_0 + a_j  \right) \\
    \beta_j  & =  b_0 + b_j \\
    p_j      & = \exp \left(  \phi_0 + \phi_j  \right) \\
\end{aligned}
\end{aligned}
\]

## Covariates
The constant one is the only covariate in this example.

## Simulated data

### Problem Settings
The following settings are used to simulate the data and check
that the solution is correct:
```python '''
import math

n_time = 21  # number of time points used in the simulation
n_group = 4  # number of groups
rel_tol = 5e-4  # relative tolerance used to check optimal solution
# simulation values used for b_0, ..., b_4
b_true = [20.0, -2.0, -1.0, +1.0, +2.0]
# simulation values used for a_0, ..., a_4
a_true = [math.log(2.0) / b_true[0], -0.2, -0.1, +0.1, +0.2]
# simulation values used for phi_0, ..., phi_4
phi_true = [math.log(0.1), -0.3, -0.15, +0.15, +0.3]
'''```
The fixed effects are initialized to be their true values divided by three.
The random effects are initialized to be zero.

### Time Grid
A grid of *n_time* points in time, \( t_i \), where
\[
    t_i = b_0 / ( n_t - 1 )
\]
where \( n_t \) is the number of time points.
The minimum value for this grid is zero and its maximum is \( b_0 \).

### Measurement values
We simulate data, \( y_{i,j} \), with no noise at each of the time points.
To be specific,
for \( i = 0 , \ldots , n_t - 1 \), \( j = 1 , \ldots , n_G  \)
\[
    y_{i,j} = f( t_i , \alpha_j , \beta_j , p_j )
\]
There is no noise in this simulated data, but when we do the fitting,
we model each data point as having noise.

## Prior
We want our result to fit the noiseless data perfectly, but there
is only data for the random effects.
We add a prior on the fixed effects to stabilize the estimation
procedure. (It would be better if we could specify that the
sum of the random effects corresponding to a fixed effect was zero.)
Each prior is specified by a mean, equal to the true value,
and a standard deviation, equal to  1/100 times the true value.
The mean must be the true value for the optimal fit to be perfect.

## Example Source Code
```python '''
# -------------------------------------------------------------------------
import scipy
import sys
import pandas
import numpy

# TODO: Ask Brad what this is
#import sandbox
#sandbox.path()

from curvefit.core.functions import expit, normal_loss
from curvefit.core.data import Data
from curvefit.core.parameter import Variable, Parameter, ParameterSet
from curvefit.models.core_model import CoreModel
from curvefit.solvers.solvers import ScipyOpt

#
# number of parameters, fixed effects, random effects
num_params = 3
num_fe = 3
num_re = num_fe * n_group

#
# true values of parameters
alpha_true = numpy.exp(a_true[0] + numpy.array(a_true[1:]))
beta_true = b_true[0] + numpy.array(b_true[1:])
p_true = numpy.exp(phi_true[0] + numpy.array(phi_true[1:]))
params_true = [alpha_true, beta_true, p_true]

#
# identity function
def identity_fun(x):
    return x


#
# link function used for alpha, p
def exp_fun(x):
    return numpy.exp(x)

#
# -----------------------------------------------------------------------
# data_frame
num_data = n_time * n_group
time_grid = numpy.array(range(n_time)) * b_true[0] / (n_time - 1)
independent_var = numpy.zeros(0, dtype=float)
measurement_value = numpy.zeros(0, dtype=float)
data_group = list()
for j in range(1, n_group + 1):
    group_j = 'group_' + str(j)
    alpha_j = math.exp(a_true[0] + a_true[j])
    beta_j = b_true[0] + b_true[j]
    p_j = math.exp(phi_true[0] + phi_true[j])
    y_j = expit(time_grid, numpy.array([alpha_j, beta_j, p_j]))
    independent_var = numpy.append(independent_var, time_grid)
    measurement_value = numpy.append(measurement_value, y_j)
    data_group += n_time * [group_j]
constant_one = num_data * [1.0]
measurement_std = num_data * [0.1]
data_dict = {
    'independent_var': independent_var,
    'measurement_value': measurement_value,
    'measurement_std': measurement_std,
    'constant_one': constant_one,
    'data_group': data_group,
}
data_frame = pandas.DataFrame(data_dict)

# ------------------------------------------------------------------------
# curve_model

data = Data(
    df=data_frame,
    col_t='independent_var',
    col_obs='measurement_value',
    col_covs=num_params * ['constant_one'],
    col_group='data_group',
    obs_space=expit,
    col_obs_se='measurement_std'
)

a_intercept = Variable(
    covariate='constant_one',
    var_link_fun=lambda x: x,
    fe_init=a_true[0]/3,
    re_init=0.0,
    fe_gprior=[a_true[0], a_true[0] / 100.0],
    fe_bounds=[-numpy.inf, numpy.inf],
    re_bounds=[-numpy.inf, numpy.inf]
)

b_intercept = Variable(
    covariate='constant_one',
    var_link_fun=lambda x: x,
    fe_init=b_true[0] / 3,
    re_init=0.0,
    fe_gprior=[b_true[0], b_true[0] / 100.0],
    fe_bounds=[-numpy.inf, numpy.inf],
    re_bounds=[-numpy.inf, numpy.inf]
)

phi_intercept = Variable(
    covariate='constant_one',
    var_link_fun=lambda x: x,
    fe_init=phi_true[0] / 3,
    re_init=0.0,
    # TODO: Originally it was [phi_true[0], phi_true[0] / 100]
    # and I don't understand why it worked
    fe_gprior=[phi_true[0], exp_fun(phi_true[0]) / 100.0],
    fe_bounds=[-numpy.inf, numpy.inf],
    re_bounds=[-numpy.inf, numpy.inf]
)

alpha = Parameter(param_name='alpha', link_fun=numpy.exp, variables=[a_intercept])
beta = Parameter(param_name='beta', link_fun=lambda x: x, variables=[b_intercept])
p = Parameter(param_name='p', link_fun=numpy.exp, variables=[phi_intercept])

parameters = ParameterSet([alpha, beta, p])

optimizer_options = {
    'disp': 0,
    'maxiter': 200,
    'ftol': 1e-8,
    'gtol': 1e-8,
}

model = CoreModel(
    param_set=parameters,
    curve_fun=expit,
    loss_fun=normal_loss
)
solver = ScipyOpt(model)
solver.fit(data=data._get_df(copy=True, return_specs=True), options=optimizer_options)
params_estimate = model.get_params(solver.x_opt, expand=False)

# TODO: Figure out why it does not pass checks
for i in range(num_fe):
    assert numpy.allclose(params_estimate[i], params_true[i], rtol=rel_tol)

print('random_effect.py: OK')
sys.exit(0)
''' ```
{end_markdown random_effect_xam}
'''
