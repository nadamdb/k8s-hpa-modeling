import itertools


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
        # Important if get_derivate_of_products is used too!
        if c < 2:
            #  raise ValueError("c must be at least 2")
            print("WARNING: c must be at least 2, might not cause problem if only expected value is calculated!")
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
            # solution index 0 means assuming the etha_c value to be the 0th value in this list, and building the rest of the calculation
            #  with this assumption.
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
            etha_c_values = self.func_etha_c(s, derivate_order=derivate_order)
            # the solution index is handled inside func_etha_c
            return etha_c_values
        elif 1 <= k < self.c:
            possible_results = []
            func_etha_k_plus_1_values = self.func_etha(k + 1, s)
            if derivate_order == 0:
                for etha_k_plus_1 in func_etha_k_plus_1_values:
                    possible_results.append(k * self.mu_ / (s + self.lambda_ - self.lambda_ * etha_k_plus_1 + k * self.mu_))
                return possible_results
            elif derivate_order == 1:
                func_etha_k_plus_1_der1_values = self.func_etha(k + 1, s, derivate_order=1)
                # if solution index is used, both lists have only one element
                for der0, der1 in itertools.product(func_etha_k_plus_1_values, func_etha_k_plus_1_der1_values):
                    possible_results.append(k * self.mu_ * (self.lambda_ * der1 - 1.0) /
                                            ((s + self.lambda_ - self.lambda_ * der0 + k * self.mu_) ** 2))
                return possible_results
            elif derivate_order == 2:
                func_etha_k_plus_1_der1_values = self.func_etha(k + 1, s, derivate_order=1)
                func_etha_k_plus_1_der2_values = self.func_etha(k + 1, s, derivate_order=2)
                # if solution index is used, all lists have only one element
                for der0, der1, der2 in itertools.product(func_etha_k_plus_1_values,
                                                          func_etha_k_plus_1_der1_values,
                                                          func_etha_k_plus_1_der2_values):
                    expr = s + self.lambda_ - self.lambda_ * der0 + k * self.mu_
                    possible_results.append( (k * self.mu_ * self.lambda_ * der2 * expr +
                                              2.0 * k * self.mu_ * ( (1.0 - self.lambda_ * der1) ** 2)) /
                                              ( expr ** 3 ) )
                return possible_results
            else:
                raise ValueError("Higher derivate order is not supported")
        else:
            raise ValueError("k must be between 1 and c")
