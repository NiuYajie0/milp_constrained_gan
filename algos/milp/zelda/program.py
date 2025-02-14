from docplex.mp.model import Model


class Program(object):
    def __init__(self, partial=False):
        """This class is a class for storing all the information about the milp we will use."""
        self._model = Model(name='zelda_heuristic_constraints')
        self._grid_width = 13
        self._is_partial = partial
        self._grid_height = 9
        self._build_program()
        self._model.print_information()

    def get_cplex_prob(self):
        return self._model.get_cplex()

    def add_gan_output(self, gan_output):
        """Use this function to add a wart start solution from gan's output"""
        warm_start = self._model.new_solution()
        for row in range(9):
            for col in range(13):
                if gan_output[row][col] == 0:
                    warm_start.add_var_value(self.W[row * 13 + col], 1)
                    warm_start.add_var_value(self.P[row * 13 + col], 0)
                    warm_start.add_var_value(self.K[row * 13 + col], 0)
                    warm_start.add_var_value(self.G[row * 13 + col], 0)
                    warm_start.add_var_value(self.E1[row * 13 + col], 0)
                    warm_start.add_var_value(self.E2[row * 13 + col], 0)
                    warm_start.add_var_value(self.E3[row * 13 + col], 0)
                elif gan_output[row][col] == 1:
                    warm_start.add_var_value(self.W[row * 13 + col], 0)
                    warm_start.add_var_value(self.P[row * 13 + col], 0)
                    warm_start.add_var_value(self.K[row * 13 + col], 0)
                    warm_start.add_var_value(self.G[row * 13 + col], 0)
                    warm_start.add_var_value(self.E1[row * 13 + col], 0)
                    warm_start.add_var_value(self.E2[row * 13 + col], 0)
                    warm_start.add_var_value(self.E3[row * 13 + col], 0)
                elif gan_output[row][col] == 2:
                    warm_start.add_var_value(self.W[row * 13 + col], 0)
                    warm_start.add_var_value(self.P[row * 13 + col], 0)
                    warm_start.add_var_value(self.K[row * 13 + col], 1)
                    warm_start.add_var_value(self.G[row * 13 + col], 0)
                    warm_start.add_var_value(self.E1[row * 13 + col], 0)
                    warm_start.add_var_value(self.E2[row * 13 + col], 0)
                    warm_start.add_var_value(self.E3[row * 13 + col], 0)
                elif gan_output[row][col] == 3:
                    warm_start.add_var_value(self.W[row * 13 + col], 0)
                    warm_start.add_var_value(self.P[row * 13 + col], 0)
                    warm_start.add_var_value(self.K[row * 13 + col], 0)
                    warm_start.add_var_value(self.G[row * 13 + col], 1)
                    warm_start.add_var_value(self.E1[row * 13 + col], 0)
                    warm_start.add_var_value(self.E2[row * 13 + col], 0)
                    warm_start.add_var_value(self.E3[row * 13 + col], 0)
                elif gan_output[row][col] == 4:
                    warm_start.add_var_value(self.W[row * 13 + col], 0)
                    warm_start.add_var_value(self.P[row * 13 + col], 0)
                    warm_start.add_var_value(self.K[row * 13 + col], 0)
                    warm_start.add_var_value(self.G[row * 13 + col], 0)
                    warm_start.add_var_value(self.E1[row * 13 + col], 1)
                    warm_start.add_var_value(self.E2[row * 13 + col], 0)
                    warm_start.add_var_value(self.E3[row * 13 + col], 0)
                elif gan_output[row][col] == 5:
                    warm_start.add_var_value(self.W[row * 13 + col], 0)
                    warm_start.add_var_value(self.P[row * 13 + col], 0)
                    warm_start.add_var_value(self.K[row * 13 + col], 0)
                    warm_start.add_var_value(self.G[row * 13 + col], 0)
                    warm_start.add_var_value(self.E1[row * 13 + col], 0)
                    warm_start.add_var_value(self.E2[row * 13 + col], 1)
                    warm_start.add_var_value(self.E3[row * 13 + col], 0)
                elif gan_output[row][col] == 6:
                    warm_start.add_var_value(self.W[row * 13 + col], 0)
                    warm_start.add_var_value(self.P[row * 13 + col], 0)
                    warm_start.add_var_value(self.K[row * 13 + col], 0)
                    warm_start.add_var_value(self.G[row * 13 + col], 0)
                    warm_start.add_var_value(self.E1[row * 13 + col], 0)
                    warm_start.add_var_value(self.E2[row * 13 + col], 0)
                    warm_start.add_var_value(self.E3[row * 13 + col], 1)
                else:
                    warm_start.add_var_value(self.W[row * 13 + col], 0)
                    warm_start.add_var_value(self.P[row * 13 + col], 1)
                    warm_start.add_var_value(self.K[row * 13 + col], 0)
                    warm_start.add_var_value(self.G[row * 13 + col], 0)
                    warm_start.add_var_value(self.E1[row * 13 + col], 0)
                    warm_start.add_var_value(self.E2[row * 13 + col], 0)
                    warm_start.add_var_value(self.E3[row * 13 + col], 0)
        self._model.add_mip_start(warm_start)

    def clean_warmstart(self):
        """Remove current warm start solution"""
        self._model.clear_mip_starts()

    def set_randomseed(self, seed):
        self._model.parameters.randomseed.set(seed)

    def get_objective_params_from_gan_output(self, gan_output):
        Wc = [0 for _ in range(9 * 13)]
        Pc = [0 for _ in range(9 * 13)]
        Kc = [0 for _ in range(9 * 13)]
        Gc = [0 for _ in range(9 * 13)]
        E1c = [0 for _ in range(9 * 13)]
        E2c = [0 for _ in range(9 * 13)]
        E3c = [0 for _ in range(9 * 13)]
        Emc = [0 for _ in range(9 * 13)]
        for row in range(9):
            for col in range(13):
                if gan_output[row][col] == 0:
                    Wc[row * 13 + col] = 1
                    Pc[row * 13 + col] = 0
                    Kc[row * 13 + col] = 0
                    Gc[row * 13 + col] = 0
                    E1c[row * 13 + col] = 0
                    E2c[row * 13 + col] = 0
                    E3c[row * 13 + col] = 0
                    Emc[row * 13 + col] = 0
                elif gan_output[row][col] == 1:
                    Wc[row * 13 + col] = 0
                    Pc[row * 13 + col] = 0
                    Kc[row * 13 + col] = 0
                    Gc[row * 13 + col] = 0
                    E1c[row * 13 + col] = 0
                    E2c[row * 13 + col] = 0
                    E3c[row * 13 + col] = 0
                    Emc[row * 13 + col] = 1
                elif gan_output[row][col] == 2:
                    Wc[row * 13 + col] = 0
                    Pc[row * 13 + col] = 0
                    Kc[row * 13 + col] = 1
                    Gc[row * 13 + col] = 0
                    E1c[row * 13 + col] = 0
                    E2c[row * 13 + col] = 0
                    E3c[row * 13 + col] = 0
                    Emc[row * 13 + col] = 0
                elif gan_output[row][col] == 3:
                    Wc[row * 13 + col] = 0
                    Pc[row * 13 + col] = 0
                    Kc[row * 13 + col] = 0
                    Gc[row * 13 + col] = 1
                    E1c[row * 13 + col] = 0
                    E2c[row * 13 + col] = 0
                    E3c[row * 13 + col] = 0
                    Emc[row * 13 + col] = 0
                elif gan_output[row][col] == 4:
                    Wc[row * 13 + col] = 0
                    Pc[row * 13 + col] = 0
                    Kc[row * 13 + col] = 0
                    Gc[row * 13 + col] = 0
                    E1c[row * 13 + col] = 1
                    E2c[row * 13 + col] = 0
                    E3c[row * 13 + col] = 0
                    Emc[row * 13 + col] = 0
                elif gan_output[row][col] == 5:
                    Wc[row * 13 + col] = 0
                    Pc[row * 13 + col] = 0
                    Kc[row * 13 + col] = 0
                    Gc[row * 13 + col] = 0
                    E1c[row * 13 + col] = 0
                    E2c[row * 13 + col] = 1
                    E3c[row * 13 + col] = 0
                    Emc[row * 13 + col] = 0
                elif gan_output[row][col] == 6:
                    Wc[row * 13 + col] = 0
                    Pc[row * 13 + col] = 0
                    Kc[row * 13 + col] = 0
                    Gc[row * 13 + col] = 0
                    E1c[row * 13 + col] = 0
                    E2c[row * 13 + col] = 0
                    E3c[row * 13 + col] = 1
                    Emc[row * 13 + col] = 0
                else:
                    Wc[row * 13 + col] = 0
                    Pc[row * 13 + col] = 1
                    Kc[row * 13 + col] = 0
                    Gc[row * 13 + col] = 0
                    E1c[row * 13 + col] = 0
                    E2c[row * 13 + col] = 0
                    E3c[row * 13 + col] = 0
                    Emc[row * 13 + col] = 0
        return Wc, Pc, Kc, Gc, E1c, E2c, E3c, Emc

    def set_objective(self, Wc, Pc, Kc, Gc, E1c, E2c, E3c, Emc):
        self._model.maximize(self._model.sum([self.W[i] * Wc[i] for i in range(len(self.W))]) +
                             self._model.sum([self.P[i] * Pc[i] for i in range(len(self.W))]) +
                             self._model.sum([self.K[i] * Kc[i] for i in range(len(self.W))]) +
                             self._model.sum([self.G[i] * Gc[i] for i in range(len(self.W))]) +
                             self._model.sum([self.E1[i] * E1c[i] for i in range(len(self.W))]) +
                             self._model.sum([self.E2[i] * E2c[i] for i in range(len(self.W))]) +
                             self._model.sum([self.E3[i] * E3c[i] for i in range(len(self.W))]) +
                             self._model.sum([(1 - self.P[i] - self.K[i] - self.G[i] - self.E1[i] - self.E2[i] -
                                               self.E3[i] - self.W[i]) * Emc[i] for i in range(len(self.W))]))

    def solve(self):
        return self._model.solve()

    def _build_program(self):
        """Use this function to build the model."""
        N = self._grid_width * self._grid_height
        # First define variables
        # these variables are defined in the same order as in the index2str json file
        # wall indicator variables, w_i in {0, 1}
        self.W = []
        for i in range(N):
            self.W.append(self._model.integer_var(name='w_{}'.format(i), ub=1))
        # empty space variables, em_i in {0, 1}
        self.Em = []
        for i in range(N):
            self.Em.append(self._model.integer_var(name='em_{}'.format(i), ub=1))
        # key indicator variables, k_i in {0, 1}
        self.K = []
        for i in range(N):
            self.K.append(self._model.integer_var(name='k_{}'.format(i), ub=1))
        # door indicator variables, g_i in {0, 1}
        self.G = []
        for i in range(N):
            self.G.append(self._model.integer_var(name='g_{}'.format(i), ub=1))
        # enemy 1 indicator variables, e1_i in {0, 1}
        self.E1 = []
        for i in range(N):
            self.E1.append(self._model.integer_var(name='e1_{}'.format(i), ub=1))
        # enemy 2 indicator variables, e2_i in {0, 1}
        self.E2 = []
        for i in range(N):
            self.E2.append(self._model.integer_var(name='e2_{}'.format(i), ub=1))
        # enemy 3 indicator variables, e3_i in {0, 1}
        self.E3 = []
        for i in range(N):
            self.E3.append(self._model.integer_var(name='e3_{}'.format(i), ub=1))
        # player indicator variables, p_i in {0, 1}
        self.P = []
        for i in range(N):
            self.P.append(self._model.integer_var(name='p_{}'.format(i), ub=1))
        if not self._is_partial:
            # X graph try to encode that the palyer should be able to reach the key
            # 1. super source node to every node inside
            Xs = []
            for i in range(N):
                Xs.append(self._model.integer_var(name='xs{}'.format(i), ub=1))
            # 2. super sind node from every node insied
            Xt = []
            for i in range(N):
                Xt.append(self._model.integer_var(name='x{}t'.format(i), ub=1))

            # 3. internal node how much in how much out

            def add_new_var(arry: list, id: str):
                if len(self._model.find_matching_vars(id)) == 0:
                    arry.append(self._model.integer_var(name=id, ub=1))
                else:
                    arry.append(self._model.find_matching_vars(id)[0])

            Xin = []
            Xout = []
            for i in range(N):
                xin = [Xs[i]]
                xout = [Xt[i]]
                if i == 0:
                    add_new_var(xin, 'x{}{}'.format(13, i))
                    add_new_var(xin, 'x{}{}'.format(1, i))
                    add_new_var(xout, 'x{}{}'.format(i, 13))
                    add_new_var(xout, 'x{}{}'.format(i, 1))
                elif i == 12:
                    add_new_var(xin, 'x{}{}'.format(11, i))
                    add_new_var(xin, 'x{}{}'.format(25, i))
                    add_new_var(xout, 'x{}{}'.format(i, 11))
                    add_new_var(xout, 'x{}{}'.format(i, 25))
                elif i == 116:
                    add_new_var(xin, 'x{}{}'.format(115, i))
                    add_new_var(xin, 'x{}{}'.format(103, i))
                    add_new_var(xout, 'x{}{}'.format(i, 115))
                    add_new_var(xout, 'x{}{}'.format(i, 103))
                elif i == 104:
                    add_new_var(xin, 'x{}{}'.format(105, i))
                    add_new_var(xin, 'x{}{}'.format(91, i))
                    add_new_var(xout, 'x{}{}'.format(i, 105))
                    add_new_var(xout, 'x{}{}'.format(i, 91))
                elif 0 < i < 12:
                    add_new_var(xin, 'x{}{}'.format(i - 1, i))
                    add_new_var(xin, 'x{}{}'.format(i + 1, i))
                    add_new_var(xin, 'x{}{}'.format(i + 13, i))
                    add_new_var(xout, 'x{}{}'.format(i, i - 1))
                    add_new_var(xout, 'x{}{}'.format(i, i + 1))
                    add_new_var(xout, 'x{}{}'.format(i, i + 13))
                elif 104 < i < 116:
                    add_new_var(xin, 'x{}{}'.format(i - 1, i))
                    add_new_var(xin, 'x{}{}'.format(i + 1, i))
                    add_new_var(xin, 'x{}{}'.format(i - 13, i))
                    add_new_var(xout, 'x{}{}'.format(i, i - 1))
                    add_new_var(xout, 'x{}{}'.format(i, i + 1))
                    add_new_var(xout, 'x{}{}'.format(i, i - 13))
                elif i % 13 == 0:
                    add_new_var(xin, 'x{}{}'.format(i - 13, i))
                    add_new_var(xin, 'x{}{}'.format(i + 1, i))
                    add_new_var(xin, 'x{}{}'.format(i + 13, i))
                    add_new_var(xout, 'x{}{}'.format(i, i - 13))
                    add_new_var(xout, 'x{}{}'.format(i, i + 1))
                    add_new_var(xout, 'x{}{}'.format(i, i + 13))
                elif i % 13 == 12:
                    add_new_var(xin, 'x{}{}'.format(i - 13, i))
                    add_new_var(xin, 'x{}{}'.format(i - 1, i))
                    add_new_var(xin, 'x{}{}'.format(i + 13, i))
                    add_new_var(xout, 'x{}{}'.format(i, i - 13))
                    add_new_var(xout, 'x{}{}'.format(i, i + 13))
                    add_new_var(xout, 'x{}{}'.format(i, i - 1))
                else:  # for internal nodes of internal nodes
                    add_new_var(xin, 'x{}{}'.format(i - 13, i))
                    add_new_var(xin, 'x{}{}'.format(i + 13, i))
                    add_new_var(xin, 'x{}{}'.format(i - 1, i))
                    add_new_var(xin, 'x{}{}'.format(i + 1, i))
                    add_new_var(xout, 'x{}{}'.format(i, i - 13))
                    add_new_var(xout, 'x{}{}'.format(i, i + 13))
                    add_new_var(xout, 'x{}{}'.format(i, i - 1))
                    add_new_var(xout, 'x{}{}'.format(i, i + 1))
                Xin.append(xin)
                Xout.append(xout)
            # Y graph try to encode that the palyer should be able to reach the door
            # 1. super source node to every node inside
            Ys = []
            for i in range(N):
                Ys.append(self._model.integer_var(name='ys{}'.format(i), ub=1))
            # 2. super sind node from every node insied
            Yt = []
            for i in range(N):
                Yt.append(self._model.integer_var(name='y{}t'.format(i), ub=1))
            # 3. internal node how much in how much out
            Yin = []
            Yout = []
            for i in range(N):
                yin = [Ys[i]]
                yout = [Yt[i]]
                if i == 0:
                    add_new_var(yin, 'y{}{}'.format(13, i))
                    add_new_var(yin, 'y{}{}'.format(1, i))
                    add_new_var(yout, 'y{}{}'.format(i, 13))
                    add_new_var(yout, 'y{}{}'.format(i, 1))
                elif i == 12:
                    add_new_var(yin, 'y{}{}'.format(11, i))
                    add_new_var(yin, 'y{}{}'.format(25, i))
                    add_new_var(yout, 'y{}{}'.format(i, 11))
                    add_new_var(yout, 'y{}{}'.format(i, 25))
                elif i == 116:
                    add_new_var(yin, 'y{}{}'.format(115, i))
                    add_new_var(yin, 'y{}{}'.format(103, i))
                    add_new_var(yout, 'y{}{}'.format(i, 115))
                    add_new_var(yout, 'y{}{}'.format(i, 103))
                elif i == 104:
                    add_new_var(yin, 'y{}{}'.format(105, i))
                    add_new_var(yin, 'y{}{}'.format(91, i))
                    add_new_var(yout, 'y{}{}'.format(i, 105))
                    add_new_var(yout, 'y{}{}'.format(i, 91))
                elif 0 < i < 12:
                    add_new_var(yin, 'y{}{}'.format(i - 1, i))
                    add_new_var(yin, 'y{}{}'.format(i + 1, i))
                    add_new_var(yin, 'y{}{}'.format(i + 13, i))
                    add_new_var(yout, 'y{}{}'.format(i, i - 1))
                    add_new_var(yout, 'y{}{}'.format(i, i + 1))
                    add_new_var(yout, 'y{}{}'.format(i, i + 13))
                elif 104 < i < 116:
                    add_new_var(yin, 'y{}{}'.format(i - 1, i))
                    add_new_var(yin, 'y{}{}'.format(i + 1, i))
                    add_new_var(yin, 'y{}{}'.format(i - 13, i))
                    add_new_var(yout, 'y{}{}'.format(i, i - 1))
                    add_new_var(yout, 'y{}{}'.format(i, i + 1))
                    add_new_var(yout, 'y{}{}'.format(i, i - 13))
                elif i % 13 == 0:
                    add_new_var(yin, 'y{}{}'.format(i - 13, i))
                    add_new_var(yin, 'y{}{}'.format(i + 1, i))
                    add_new_var(yin, 'y{}{}'.format(i + 13, i))
                    add_new_var(yout, 'y{}{}'.format(i, i - 13))
                    add_new_var(yout, 'y{}{}'.format(i, i + 1))
                    add_new_var(yout, 'y{}{}'.format(i, i + 13))
                elif i % 13 == 12:
                    add_new_var(yin, 'y{}{}'.format(i - 13, i))
                    add_new_var(yin, 'y{}{}'.format(i - 1, i))
                    add_new_var(yin, 'y{}{}'.format(i + 13, i))
                    add_new_var(yout, 'y{}{}'.format(i, i - 13))
                    add_new_var(yout, 'y{}{}'.format(i, i + 13))
                    add_new_var(yout, 'y{}{}'.format(i, i - 1))
                else:  # for internal nodes of internal nodes
                    add_new_var(yin, 'y{}{}'.format(i - 13, i))
                    add_new_var(yin, 'y{}{}'.format(i + 13, i))
                    add_new_var(yin, 'y{}{}'.format(i - 1, i))
                    add_new_var(yin, 'y{}{}'.format(i + 1, i))
                    add_new_var(yout, 'y{}{}'.format(i, i - 13))
                    add_new_var(yout, 'y{}{}'.format(i, i + 13))
                    add_new_var(yout, 'y{}{}'.format(i, i - 1))
                    add_new_var(yout, 'y{}{}'.format(i, i + 1))
                Yin.append(yin)
                Yout.append(yout)

        # now define constraints
        # 1. for every tile there could be one type or empty
        for i in range(N):
            self._model.add_constraint(
                self.W[i] + self.G[i] + self.K[i] + self.P[i] + self.E1[i] + self.E2[i] + self.E3[i] + self.Em[i] == 1)
        # 2. in one grid, there could be only one goal, player, key
        self._model.add_constraint(self._model.sum(self.G) == 1)
        self._model.add_constraint(self._model.sum(self.K) == 1)
        self._model.add_constraint(self._model.sum(self.P) == 1)
        # 3. The border of the grid should be walls
        self._model.add_constraint(self._model.sum(self.W[0:13]) == 13)
        self._model.add_constraint(self._model.sum(self.W[104:117]) == 13)
        self._model.add_constraint(self._model.sum([self.W[i * 13] for i in range(9)]) == 9)
        self._model.add_constraint(self._model.sum([self.W[i * 13 + 12] for i in range(9)]) == 9)
        if not self._is_partial:
            # 4. The number of enemies should be less than 0.6 percent of empty space
            self._model.add_constraint(self._model.sum(self.Em) * 0.6 >=
                                       self._model.sum(self.E1) + self._model.sum(self.E2) + self._model.sum(self.E3))
            # 5. the player should be able to reach the key, X graph
            # 5.1 super source will only go into player node
            self._model.add_constraint(self._model.sum(Xs) == 1)
            for i in range(N):
                self._model.add_constraint(Xs[i] - self.P[i] == 0)
            # 5.2 the flow will only be pushed into super sink from the key node
            self._model.add_constraint(self._model.sum(Xt) == 1)
            for i in range(N):
                self._model.add_constraint(Xt[i] - self.K[i] == 0)
            # 5.3 for every internal node there how much in how much out
            for i in range(N):
                self._model.add_constraint(self._model.sum(Xin[i]) - self._model.sum(Xout[i]) == 0)
            # 5.4 for every internal node the wall node will not be used
            for i in range(N):
                self._model.add_constraint(self._model.sum(Xin[i]) + self.W[i] <= 1)
                self._model.add_constraint(self._model.sum(Xout[i]) + self.W[i] <= 1)
            # 6. the player should be able to reach the door, Y graph
            # 6.1 super source will only go into player node
            self._model.add_constraint(self._model.sum(Ys) == 1)
            for i in range(N):
                self._model.add_constraint(Ys[i] - self.P[i] == 0)
            # 6.2 the flow will only be pushed into super sink from the door node
            self._model.add_constraint(self._model.sum(Yt) == 1)
            for i in range(N):
                self._model.add_constraint(Yt[i] - self.G[i] == 0)
            # 6.3 for every internal node there how much in how much out
            for i in range(N):
                self._model.add_constraint(self._model.sum(Yin[i]) - self._model.sum(Yout[i]) == 0)
            # 6.4 for every internal node the wall node will not be used
            for i in range(N):
                self._model.add_constraint(self._model.sum(Yin[i]) + self.W[i] <= 1)
                self._model.add_constraint(self._model.sum(Yout[i]) + self.W[i] <= 1)
            # 7 there must be at least one enemy
            # for i in range(N):
            #     self._model.add_constraint(self._model.sum(self.E1 + self.E2 + self.E3) >= 1)


if __name__ == '__main__':
    program = Program()

    si = program.solve()
    print(si)
