import torch
from torch.autograd import Function

from .util import bger, expandParam, extract_nBatch
from . import solvers
from .solvers.pdipm import batch as pdipm_b
from .solvers.pdipm import spbatch as pdipm_spb
# from .solvers.pdipm import single as pdipm_s

from enum import Enum

import cplex
import numpy as np


def forward_single_np_gurobi(Q, p, G, h, A, b):
    '''
    Convert to Gurobi model. Copied from 
    https://github.com/stephane-caron/qpsolvers/blob/master/qpsolvers/gurobi_.py
    '''
    n = Q.shape[1]
    model = cplex.Cplex()
    model.set_log_stream(None)
    model.set_results_stream(None)
    model.set_warning_stream(None)

    infty = cplex.infinity
    x = model.variables.add(obj=list(p.astype(float)),
        lb=n*[-cplex.infinity],
        ub=n*[cplex.infinity], 
        names=["x{}".format(i) for i in range(n)])

    # minimize
    #     x.T * Q * x + p * x
    for i,j in zip(*Q.nonzero()):
        model.objective.set_quadratic_coefficients(int(i),int(j),float(Q[i,j]))

    for i in range(n):
        model.objective.set_linear(i, float(p[i]))

    model.objective.set_sense(model.objective.sense.minimize)

    # subject to
    #     G * x <= h
    # inequality_constraints = []
    if G is not None:
        for i in range(G.shape[0]):
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind = range(n), val = [float(x) for x in G[i]])],
                senses=['L'],
                rhs=[h[i]])

    # subject to
    #     A * x == b
    equality_constraints = []
    if A is not None:
        for i in range(A.shape[0]):
            model.linear_constraints.add(
                lin_expr=[cplex.SparsePair(ind = range(n), val = [float(x) for x in A[i]])],
                senses=['E'],
                rhs=[b[i]])

    # model.write("/Users/aaronferber/Desktop/debug.lp")
    model.solve()

    x_opt = np.array(model.solution.get_values())
    slacks = -(G@x_opt - h)
    
    # lam = np.array([inequality_constraints[i].pi for i in range(len(inequality_constraints))])
    lam = np.array(model.solution.get_dual_values()[:G.shape[0]])
    # nu = np.array([equality_constraints[i].pi for i in range(len(equality_constraints))])
    nu = np.array(model.solution.get_dual_values()[-A.shape[0]:])

    return model.solution.get_objective_value(), x_opt, nu, lam, slacks


# def forward_single_np_gurobi(Q, p, G, h, A, b):
#     import gurobipy as gp
#     import numpy as np
#     '''
#     Convert to Gurobi model. Copied from 
#     https://github.com/stephane-caron/qpsolvers/blob/master/qpsolvers/gurobi_.py
#     '''
#     n = Q.shape[1]
#     model = gp.Model()
#     model.params.OutputFlag = 0
#     x = [model.addVar(
#             vtype=gp.GRB.INTEGER,
#             name='x_%d' % i,
#             lb=-gp.GRB.INFINITY,
#             ub=+gp.GRB.INFINITY)
#         for i in range(n)
#     ]
#     model.update()   # integrate new variables

#     # minimize
#     #     x.T * Q * x + p * x
#     obj = gp.QuadExpr()
#     rows, cols = Q.nonzero()
#     for i, j in zip(rows, cols):
#         obj += x[i] * Q[i, j] * x[j]
#     for i in range(n):
#         obj += p[i] * x[i]
#     model.setObjective(obj, gp.GRB.MINIMIZE)

#     # subject to
#     #     G * x <= h
#     inequality_constraints = []
#     if G is not None:
#         for i in range(G.shape[0]):
#             row = np.where(G[i] != 0)[0]
#             inequality_constraints.append(model.addConstr(gp.quicksum(G[i, j] * x[j] for j in row) <= h[i]))

#     # subject to
#     #     A * x == b
#     equality_constraints = []
#     if A is not None:
#         for i in range(A.shape[0]):
#             row = np.where(A[i] != 0)[0]
#             equality_constraints.append(model.addConstr(gp.quicksum(A[i, j] * x[j] for j in row) == b[i]))
#     model.update()

#     model.write("/Users/aaronferber/Desktop/debug.mps")
#     model.optimize()
#     x_opt = np.array([x[i].x for i in range(len(x))])
#     slacks = -(G@x_opt - h)


#     lam = np.array([inequality_constraints[i].pi for i in range(len(inequality_constraints))])
#     nu = np.array([equality_constraints[i].pi for i in range(len(equality_constraints))])

#     return model.ObjVal, x_opt, nu, lam, slacks

def make_gurobi_model(G, h, A, b, Q):
    import gurobipy as gp
    import numpy as np
    '''
    Convert to Gurobi model. Copied from 
    https://github.com/stephane-caron/qpsolvers/blob/master/qpsolvers/gurobi_.py
    '''
    n = A.shape[1] if A is not None else G.shape[1]
    model = gp.Model()
    model.params.OutputFlag = 0
    x = [model.addVar(
            vtype=gp.GRB.CONTINUOUS,
            name='x_%d' % i,
            lb=-gp.GRB.INFINITY,
            ub=+gp.GRB.INFINITY)
        for i in range(n)
    ]
    model.update()   # integrate new variables

    # subject to
    #     G * x <= h
    inequality_constraints = []
    if G is not None:
        for i in range(G.shape[0]):
            row = np.where(G[i] != 0)[0]
            inequality_constraints.append(model.addConstr(gp.quicksum(G[i, j] * x[j] for j in row) <= h[i]))

    # subject to
    #     A * x == b
    equality_constraints = []
    if A is not None:
        for i in range(A.shape[0]):
            row = np.where(A[i] != 0)[0]
            equality_constraints.append(model.addConstr(gp.quicksum(A[i, j] * x[j] for j in row) == b[i]))

    obj = gp.QuadExpr()
    if Q is not None:
        rows, cols = Q.nonzero()
        for i, j in zip(rows, cols):
            obj += x[i] * Q[i, j] * x[j]

    return model, x, inequality_constraints, equality_constraints, obj

def forward_gurobi_prebuilt(Q, p, model, x, inequality_constraints, equality_constraints, G, h, quadobj):
    import gurobipy as gp
    import numpy as np
    obj = gp.QuadExpr()
    obj += quadobj
    for i in range(len(p)):
        obj += p[i] * x[i]
    model.setObjective(obj, gp.GRB.MINIMIZE)
    model.optimize()
    x_opt = np.array([x[i].x for i in range(len(x))])
    if G is not None:
        print("G shape", G.shape)
        print("x_opt shape", x_opt.shape)
        print("h shape", h.shape)
        slacks = -(G@x_opt - h)
    else:
        slacks = np.array([])
    lam = np.array([inequality_constraints[i].pi for i in range(len(inequality_constraints))])
    nu = np.array([equality_constraints[i].pi for i in range(len(equality_constraints))])

    return model.ObjVal, x_opt, nu, lam, slacks



class QPSolvers(Enum):
    PDIPM_BATCHED = 1
    CVXPY = 2
    GUROBI = 3
    CUSTOM = 4


class QPFunction(Function):
    def __init__(self, eps=1e-12, verbose=0, notImprovedLim=5,
                 maxIter=20, solver=QPSolvers.PDIPM_BATCHED, model_params = None, custom_solver=None):
        self.eps = eps
        self.verbose = verbose
        self.notImprovedLim = notImprovedLim
        self.maxIter = maxIter
        self.solver = solver
        self.custom_solver = custom_solver
#        self.constant_constraints = constant_constraints
        
        if model_params is not None:
#        if constant_constraints:
#            self.A = A
#            self.b = b
#            self.G = G
#            self.h = h
#            A_arg = A.detach().numpy() if A is not None else None
#            b_arg = b.detach().numpy() if b is not None else None
#            G_arg = G.detach().numpy() if G is not None else None
#            h_arg = h.detach().numpy() if h is not None else None
#            Q_arg = Q.detach().numpy() if Q is not None else None
#            model, x, inequality_constraints, equality_constraints, obj = make_gurobi_model(G_arg,
#                                                        h_arg, A_arg, b_arg, Q_arg)
            model, x, inequality_constraints, equality_constraints, obj = model_params
            self.model = model
            self.x = x
            self.inequality_constraints = inequality_constraints
            self.equality_constraints = equality_constraints
            self.quadobj = obj
        else:
            self.model = None

    # @profile
    def forward(self, Q_, p_, G_, h_, A_, b_):
        """Solve a batch of QPs.

        This function solves a batch of QPs, each optimizing over
        `nz` variables and having `nineq` inequality constraints
        and `neq` equality constraints.
        The optimization problem for each instance in the batch
        (dropping indexing from the notation) is of the form

            \hat z =   argmin_z 1/2 z^T Q z + p^T z
                     subject to Gz <= h
                                Az  = b

        where Q \in S^{nz,nz},
              S^{nz,nz} is the set of all positive semi-definite matrices,
              p \in R^{nz}
              G \in R^{nineq,nz}
              h \in R^{nineq}
              A \in R^{neq,nz}
              b \in R^{neq}

        These parameters should all be passed to this function as
        Variable- or Parameter-wrapped Tensors.
        (See torch.autograd.Variable and torch.nn.parameter.Parameter)

        If you want to solve a batch of QPs where `nz`, `nineq` and `neq`
        are the same, but some of the contents differ across the
        minibatch, you can pass in tensors in the standard way
        where the first dimension indicates the batch example.
        This can be done with some or all of the coefficients.

        You do not need to add an extra dimension to coefficients
        that will not change across all of the minibatch examples.
        This function is able to infer such cases.

        If you don't want to use any equality or inequality constraints,
        you can set the appropriate values to:

            e = Variable(torch.Tensor())

        Parameters:
          Q:  A (nBatch, nz, nz) or (nz, nz) Tensor.
          p:  A (nBatch, nz) or (nz) Tensor.
          G:  A (nBatch, nineq, nz) or (nineq, nz) Tensor.
          h:  A (nBatch, nineq) or (nineq) Tensor.
          A:  A (nBatch, neq, nz) or (neq, nz) Tensor.
          b:  A (nBatch, neq) or (neq) Tensor.

        Returns: \hat z: a (nBatch, nz) Tensor.
        """
        nBatch = extract_nBatch(Q_, p_, G_, h_, A_, b_)
        Q, _ = expandParam(Q_, nBatch, 3)
        p, _ = expandParam(p_, nBatch, 2)
        G, _ = expandParam(G_, nBatch, 3)
        h, _ = expandParam(h_, nBatch, 2)
        A, _ = expandParam(A_, nBatch, 3)
        b, _ = expandParam(b_, nBatch, 2)

        _, nineq, nz = G.size()
        neq = A.size(1) if A.nelement() > 0 else 0
        assert(neq > 0 or nineq > 0)
        self.neq, self.nineq, self.nz = neq, nineq, nz

        if self.solver == QPSolvers.PDIPM_BATCHED:
            self.Q_LU, self.S_LU, self.R = pdipm_b.pre_factor_kkt(Q, G, A)
            zhats, self.nus, self.lams, self.slacks = pdipm_b.forward(
                Q, p, G, h, A, b, self.Q_LU, self.S_LU, self.R,
                self.eps, self.verbose, self.notImprovedLim, self.maxIter)
        elif self.solver == QPSolvers.CVXPY:
            vals = torch.Tensor(nBatch).type_as(Q)
            zhats = torch.Tensor(nBatch, self.nz).type_as(Q)
            lams = torch.Tensor(nBatch, self.nineq).type_as(Q)
            nus = torch.Tensor(nBatch, self.neq).type_as(Q)
            slacks = torch.Tensor(nBatch, self.nineq).type_as(Q)
            for i in range(nBatch):
                Ai, bi = (A[i], b[i]) if neq > 0 else (None, None)
                vals[i], zhati, nui, lami, si = solvers.cvxpy.forward_single_np(
                    *[x.cpu().detach().numpy() if x is not None else None
                      for x in (Q[i], p[i], G[i], h[i], Ai, bi)])
                zhats[i] = torch.Tensor(zhati)
                lams[i] = torch.Tensor(lami)
                slacks[i] = torch.Tensor(si)
                if neq > 0:
                    nus[i] = torch.Tensor(nui)

            self.vals = vals
            self.lams = lams
            self.nus = nus
            self.slacks = slacks
        elif self.solver == QPSolvers.GUROBI:
            vals = torch.Tensor(nBatch).type_as(Q)
            zhats = torch.Tensor(nBatch, self.nz).type_as(Q)
            lams = torch.Tensor(nBatch, self.nineq).type_as(Q)
            if self.neq > 0:
                nus = torch.Tensor(nBatch, self.neq).type_as(Q)
            else:
                nus = torch.Tensor().type_as(Q)
            slacks = torch.Tensor(nBatch, self.nineq).type_as(Q)
            for i in range(nBatch):
                Ai, bi = (A[i], b[i]) if neq > 0 else (None, None)
                if self.model is None:
                    vals[i], zhati, nui, lami, si = forward_single_np_gurobi(
                        *[x.cpu().detach().numpy() if x is not None else None
                          for x in (Q[i], p[i], G[i], h[i], Ai, bi)])
                else:
                    Gi = G[i].detach().numpy() if G is not None else None
                    hi = h[i].detach().numpy() if h is not None else None
                    vals[i], zhati, nui, lami, si = forward_gurobi_prebuilt(
                            Q[i].detach().numpy(), p[i].detach().numpy(), self.model, self.x, self.inequality_constraints, 
                            self.equality_constraints, Gi, hi, self.quadobj)
                zhats[i] = torch.Tensor(zhati)
                lams[i] = torch.Tensor(lami)
                slacks[i] = torch.Tensor(si)
                if neq > 0:
                    nus[i] = torch.Tensor(nui)

            self.vals = vals
            self.lams = lams
            self.nus = nus
            self.slacks = slacks
        elif self.solver == QPSolvers.CUSTOM:
            vals = torch.Tensor(nBatch).type_as(Q)
            zhats = torch.Tensor(nBatch, self.nz).type_as(Q)
            lams = torch.Tensor(nBatch, self.nineq).type_as(Q)
            if self.neq > 0:
                nus = torch.Tensor(nBatch, self.neq).type_as(Q)
            else:
                nus = torch.Tensor().type_as(Q)
            slacks = torch.Tensor(nBatch, self.nineq).type_as(Q)
            for i in range(nBatch):
                Ai, bi = (A[i], b[i]) if neq > 0 else (None, None)
                if self.model is None:
                    vals[i], zhati, nui, lami, si = self.custom_solver(
                        *[x.cpu().detach().numpy() if x is not None else None
                          for x in (Q[i], p[i], G[i], h[i], Ai, bi)])
                zhats[i] = torch.Tensor(zhati)
                lams[i] = torch.Tensor(lami)
                slacks[i] = torch.Tensor(si)
                if neq > 0:
                    nus[i] = torch.Tensor(nui)
            
            self.vals = vals
            self.lams = lams
            self.nus = nus
            self.slacks = slacks

            

        else:
            assert False
        # self.save_for_backward(zhats, Q_, p_, G_, h_, A_, b_)
        self.zhats = zhats
        self.Q_ = Q_
        self.p_ = p_
        self.G_ = G_
        self.h_ = h_
        self.A_ = A_
        self.b_ = b_
        return zhats

    # @profile
    def backward(self, dl_dzhat):

        # TODO: figure out how to type all these tensors correctly
        zhats = self.zhats
        Q = self.Q_
        G = self.G_.type_as(Q)
        p = self.p_.type_as(Q)
        h = self.h_.type_as(Q)
        A = self.A_.type_as(Q)
        b = self.b_.type_as(Q)
        # import IPython, sys; IPython.embed(); sys.exit(-1)
        # zhats, Q, p, G, h, A, b = self.saved_tensors
        nBatch = extract_nBatch(Q, p, G, h, A, b)
        Q, Q_e = expandParam(Q, nBatch, 3)
        p, p_e = expandParam(p, nBatch, 2)
        G, G_e = expandParam(G, nBatch, 3)
        h, h_e = expandParam(h, nBatch, 2)
        A, A_e = expandParam(A, nBatch, 3)
        b, b_e = expandParam(b, nBatch, 2)

        # neq, nineq, nz = self.neq, self.nineq, self.nz
        neq, nineq = self.neq, self.nineq


        if self.solver != QPSolvers.PDIPM_BATCHED:
            self.Q_LU, self.S_LU, self.R = pdipm_b.pre_factor_kkt(Q, G, A)

        # Clamp here to avoid issues coming up when the slacks are too small.
        # TODO: A better fix would be to get lams and slacks from the
        # solver that don't have this issue.
        d = torch.clamp(self.lams, min=1e-8) / torch.clamp(self.slacks, min=1e-8)

        pdipm_b.factor_kkt(self.S_LU, self.R.type_as(Q), d.type_as(Q))
        dx, _, dlam, dnu = pdipm_b.solve_kkt(
            self.Q_LU, d, G, A, self.S_LU,
            dl_dzhat, torch.zeros(nBatch, nineq).type_as(G),
            torch.zeros(nBatch, nineq).type_as(G),
            torch.zeros(nBatch, neq).type_as(G) if neq > 0 else torch.Tensor())

        dps = dx
        dGs = bger(dlam, zhats) + bger(self.lams, dx)
        if G_e:
            dGs = dGs.mean(0).squeeze(0)
        dhs = -dlam
        if h_e:
            dhs = dhs.mean(0).squeeze(0)
        if neq > 0:
            dAs = bger(dnu, zhats) + bger(self.nus, dx)
            dbs = -dnu
            if A_e:
                dAs = dAs.mean(0).squeeze(0)
            if b_e:
                dbs = dbs.mean(0).squeeze(0)
        else:
            dAs, dbs = None, None
        dQs = 0.5 * (bger(dx, zhats) + bger(zhats, dx))
        if Q_e:
            dQs = dQs.mean(0).squeeze(0)
        if p_e:
            dps = dps.mean(0).squeeze(0)

        grads = (dQs.float(), dps.float(), dGs.float(), dhs.float(), dAs.float(), dbs.float())

        return grads


class SpQPFunction(Function):
    def __init__(self, Qi, Qsz, Gi, Gsz, Ai, Asz,
                 eps=1e-12, verbose=0, notImprovedLim=3, maxIter=20):
        self.Qi, self.Qsz = Qi, Qsz
        self.Gi, self.Gsz = Gi, Gsz
        self.Ai, self.Asz = Ai, Asz

        self.eps = eps
        self.verbose = verbose
        self.notImprovedLim = notImprovedLim
        self.maxIter = maxIter

        self.nineq, self.nz = Gsz
        self.neq, _ = Asz

    def forward(self, Qv, p, Gv, h, Av, b):
        self.nBatch = Qv.size(0)

        zhats, self.nus, self.lams, self.slacks = pdipm_spb.forward(
            self.Qi, Qv, self.Qsz, p, self.Gi, Gv, self.Gsz, h,
            self.Ai, Av, self.Asz, b, self.eps, self.verbose,
            self.notImprovedLim, self.maxIter)

        self.save_for_backward(zhats, Qv, p, Gv, h, Av, b)
        return zhats

    def backward(self, dl_dzhat):
        zhats, Qv, p, Gv, h, Av, b = self.saved_tensors

        Di = type(self.Qi)([range(self.nineq), range(self.nineq)])
        Dv = self.lams / self.slacks
        Dsz = torch.Size([self.nineq, self.nineq])
        dx, _, dlam, dnu = pdipm_spb.solve_kkt(
            self.Qi, Qv, self.Qsz, Di, Dv, Dsz,
            self.Gi, Gv, self.Gsz,
            self.Ai, Av, self.Asz, dl_dzhat,
            type(p)(self.nBatch, self.nineq).zero_(),
            type(p)(self.nBatch, self.nineq).zero_(),
            type(p)(self.nBatch, self.neq).zero_())

        dps = dx

        dGs = bger(dlam, zhats) + bger(self.lams, dx)
        GM = torch.sparse.DoubleTensor(
            self.Gi, Gv[0].clone().fill_(1.0), self.Gsz
        ).to_dense().byte().expand_as(dGs)
        dGs = dGs[GM].view_as(Gv)

        dhs = -dlam

        dAs = bger(dnu, zhats) + bger(self.nus, dx)
        AM = torch.sparse.DoubleTensor(
            self.Ai, Av[0].clone().fill_(1.0), self.Asz
        ).to_dense().byte().expand_as(dAs)
        dAs = dAs[AM].view_as(Av)

        dbs = -dnu

        dQs = 0.5 * (bger(dx, zhats) + bger(zhats, dx))
        QM = torch.sparse.DoubleTensor(
            self.Qi, Qv[0].clone().fill_(1.0), self.Qsz
        ).to_dense().byte().expand_as(dQs)
        dQs = dQs[QM].view_as(Qv)

        grads = (dQs, dps, dGs, dhs, dAs, dbs)

        return grads
