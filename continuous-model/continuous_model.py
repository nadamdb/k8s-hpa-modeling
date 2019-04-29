

class MMcAnalyzer(object):

    def __init__(self, lambda_, mu_, c, solution_pair_index=None):
        """
        Models an M/M/c queue.

        :param solution_pair_index: if not given, all combinations are considered, if integer is given, only that index is considered.
        :param lambda_:
        :param mu_:
        :param c:
        """
        self.solution_pair_index = solution_pair_index
        if c < 2:
            raise ValueError("c must be at least 2")
        self.c = c
        self.mu_ = float(mu_)
        self.lambda_ = float(lambda_)
        if lambda_ >= c * mu_:
            raise ValueError("lamba < c * mu must be satisfied, otherwise expected value is unbounded")

    def p_dep(self, k):
        """
        Probability of a departure if there are currently k active servers.

        :param k:
        :return:
        """
        if 1 > k > self.c:
            raise ValueError("k must be between 1 and c")
        return k * self.mu_ / (self.lambda_ + k * self.mu_)

    def p_arr(self, k):
        """
        Probability of an arrival if there are currently k active servers.

        :param k:
        :return:
        """
        if 1 > k > self.c:
            raise ValueError("k must be between 1 and c")
        return self.lambda_ / (self.lambda_ + k * self.mu_)

    def func_upsilon(self, k, s, derivate_order=0):
        """
        LST of the inter-arrival time random variable if there are k busy servers.

        :param k:
        :param s:
        :return:
        """
        if derivate_order == 0:
            return (self.lambda_ + k * self.mu_) / (s + self.lambda_ + k * self.mu_)
        elif derivate_order == 1:
            return -1 / ((s + self.lambda_ + k * self.mu_) ** 2)
        elif derivate_order == 2:
            return 2 / ((s + self.lambda_ + k * self.mu_) ** 3)
        else:
            raise ValueError("Higher derivate order is not supported")

    def func_etha_c(self, s, derivate_order=0):
        """
        LST of the busy period T_c as defined in K. Omahen, V. Marathe -- Analysis & Applications of the Delay Cycle for the M/M/c Queueing
        System. 1975.

        :param s:
        :param derivate_order:
        :return: list of values, each of them being a possible solution
        """
        if s != 0:
            raise ValueError("s can only be 0")
        if derivate_order == 0:
            solutions = [1.0,
                        self.c * self.mu_ / self.lambda_]
        elif derivate_order == 1:
            # NOTE : the second element is POSITIV, its (-1)* cannot be the extected value of T_c
            solutions = [1 / (self.lambda_ - self.c * self.mu_),
                        self.c * self.mu_ / (self.lambda_ * self.c * self.mu_ - (self.lambda_ ** 2))]
        elif derivate_order == 2:
            # NOTE: the 2th element is Negative, it cannot be the second moment of T_c
            # NOTE: the latter two elements are the combination of the solutions for 0th and 1st order derivatives
            solutions = [2 * self.c * self.mu_ / ((self.c * self.mu_ - self.lambda_) ** 3),
                         -2 * self.c * self.mu_ * self.lambda_ / ((self.c * self.mu_ - self.lambda_) ** 2),
                         2 * ((self.c * self.mu_) ** 2) / self.lambda_ / ((self.c * self.mu_ - self.lambda_) ** 3),
                         2 * self.lambda_ / ((self.lambda_ - self.c * self.mu_) ** 2)]
        else:
            raise ValueError("Higher derivate order is not supported")
        if self.solution_pair_index is not None:
            return [solutions[self.solution_pair_index]]
        else:
            return solutions


# TODO: make function decorator for checking the cache on all input parameters (usable for etha and delta, IF ONLY the parameter sets are
#  always different. Only useful if we use the combination, otherwise caching is not neccesary.

class SingleSlopeWeightedBusyTimeMMcAnalyer(MMcAnalyzer):

    def __init__(self, lambda_, mu_, c):
        """
        Models the weighted busy time only until the first occurance of an empty/non-busy (k=0) system state.
        The predictions are the best, when the server is loaded, k is big and the time intervals for checking the average CPU utilization
        is short.

        :param lambda_:
        :param mu_:
        :param c:
        """
        super(SingleSlopeWeightedBusyTimeMMcAnalyer, self).__init__(lambda_, mu_, c)

    def func_etha(self, k, s, derivate_order=0):
        """
        LST of the busy period T_k as defined in K. Omahen, V. Marathe -- Analysis & Applications of the Delay Cycle for the M/M/c Queueing
        System. 1975.


        :param k:
        :param s:
        :param derivate_order:
        :return:
        """
        if k == self.c:
            # returns with a sorted list!
            return self.func_etha_c(s, derivate_order=derivate_order)
        else:
            # TODO: use self.solutioin_index!!
            possible_results = []
            if derivate_order == 0:
                func_etha_k_plus_1_values = self.func_etha(k + 1, s)
                for etha_k_plus_1 in func_etha_k_plus_1_values:
                    possible_results.append(k * self.mu_ / (s + self.lambda_ - self.lambda_ * etha_k_plus_1 + k * self.mu_))
                return set(possible_results)

    # TODO: implement other functinos of the SingleSlope model, and use the solution indexes!!