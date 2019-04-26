import itertools
import sys

sys.setrecursionlimit(100000)


class MMc_WeightedBusyTimeAnalyzer(object):

    def __init__(self, lambda_, mu_, c, n1=1, n2=1, nc=100):
        """
        Models an M/M/c queue.

        :param lambda_:
        :param mu_:
        :param c:
        """
        self.n2 = n2
        self.n1 = n1
        self.nc = nc
        if c < 2:
            raise ValueError("c must be at least 2")
        self.c = c
        self.mu_ = float(mu_)
        self.lambda_ = float(lambda_)
        if lambda_ >= c * mu_:
            raise ValueError("lamba < c * mu must be satisfied, otherwise expected value is unbounded")
        # keyed by 4-tuples of (k, current_n1, current_n2, current_nc)
        self.cache = {}

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

    def get_cache(self, cache_key):
        if cache_key in self.cache:
            return self.cache[cache_key]
        else:
            return None

    def set_cache(self, cache_key, value_list):
        if cache_key in self.cache:
            raise Exception("Cache cannot be updated")
        else:
            self.cache[cache_key] = value_list

    def func_delta_der0(self, k, s, current_n1=None, current_n2=None, current_nc=None):
        """
        Recursive definition of the LST of the weighted busy time starting from k busy servers.

        :param k:
        :param s:
        :param current_n1:
        :param current_n2:
        :return:
        """
        if current_n1 is None:
            current_n1 = self.n1
        if current_n2 is None:
            current_n2 = self.n2
        if current_nc is None:
            current_nc = self.nc
        if k < 1 or k > self.c:
            raise ValueError("k must be between 1 and c")
        final_solution_list = []
        cache_key = (k, current_n1, current_n2, current_nc)
        cache = self.get_cache(cache_key)
        if cache is not None:
            return cache
        if k == 1:
            # the inner recursion is collecting all 1 --> 2 transitions, which is described by n2.
            if current_n2 == 0:
                if current_n1 == 0:
                    # self.func_upsilon(k, s) * (self.p_dep(k) + self.p_arr(k)), but the second == 1 always
                    final_solution_list = [self.func_upsilon(1, s)]
                    self.set_cache(cache_key, final_solution_list)
                    return final_solution_list
                else:
                    # we have reached the bottom (k==1), taken enough 1 --> 2 transitions into account for this single 0 --> 1 transition.
                    possible_solutions_prev_rec = self.func_delta_der0(1, s, current_n1 - 1, self.n2, current_nc)
                    for delta_value in possible_solutions_prev_rec:
                         final_solution_list.append( self.func_upsilon(1, s) * (self.p_dep(1) * delta_value + self.p_arr(1)) )
                    final_solution_list = set(final_solution_list)
                    self.set_cache(cache_key, final_solution_list)
                    return final_solution_list
            else:
                if current_n1 == 0:
                    # we have reached the bottom (k==1), but we still need to consider some more 1 --> 2 transitions for this last 0 -->
                    # 1 transition.
                    possible_solutions_prev_rec = self.func_delta_der0(2, s, 0, current_n2 - 1, current_nc)
                    for delta_value in possible_solutions_prev_rec:
                        final_solution_list.append( self.func_upsilon(1, s) * (self.p_dep(1) + self.p_arr(1) * delta_value) )
                    final_solution_list = set(final_solution_list)
                    self.set_cache(cache_key, final_solution_list)
                    return final_solution_list
                else:
                    # we have reached the bottom (k==1), but we still need to consider some more 1 --> 2 transitions and some more 0 -->
                    # 1 transitions.
                    # so we decrease the desired number of 1 --> 2 transitions.
                    possible_solutions_prev_rec_1_2 = self.func_delta_der0(2, s, current_n1, current_n2 - 1, current_nc)
                    # so we decrease the desired number of 0 --> 1 transitions.
                    possible_solutions_prev_rec_0_1 = self.func_delta_der0(1, s, current_n1 - 1, current_n2, current_nc)
                    for delta_trans_0_1, delta_trans_1_2 in itertools.product(possible_solutions_prev_rec_0_1,
                                                                              possible_solutions_prev_rec_1_2):
                        final_solution_list.append(self.func_upsilon(1, s) * (self.p_dep(1) * delta_trans_0_1 +
                                                                              self.p_arr(1) * delta_trans_1_2))
                    final_solution_list = set(final_solution_list)
                    self.set_cache(cache_key, final_solution_list)
                    return final_solution_list
        if k == self.c:
            # this can have multiple values based on the 0th order derivate of etha_c (s). we cannot discard values here,
            # only we have the negativity / positivity constraints at the 1st and 2nd order derivates of delta.
            etha_c_values = self.func_etha_c(self.c * s)
            if current_nc == 0:
                possible_solutions_prev_rec = [1]
            else:
                # Multiple values might come from evaluating the delta
                # we didn't reach bottom, n1, n2 stays the same.
                possible_solutions_prev_rec = self.func_delta_der0(self.c - 1, s, current_n1, current_n2, current_nc - 1)
            for etha_c_value, delta_value in itertools.product(etha_c_values, possible_solutions_prev_rec):
                final_solution_list.append(etha_c_value * delta_value / float(self.c))
            final_solution_list = set(final_solution_list)
            self.set_cache(cache_key, final_solution_list)
            return final_solution_list
        else:
            # else: 1 < k < c
            possible_solutions_dep = self.func_delta_der0(k - 1, s, current_n1, current_n2, current_nc)
            possible_solutions_arr = self.func_delta_der0(k + 1, s, current_n1, current_n2, current_nc)
            for delta_arr, delta_dep in itertools.product(possible_solutions_arr, possible_solutions_dep):
                final_solution_list.append(self.func_upsilon(k, k * s) / float(k) * (self.p_dep(k) * delta_dep + self.p_arr(k) * delta_arr))
            final_solution_list = set(final_solution_list)
            self.set_cache(cache_key, final_solution_list)
            return final_solution_list

    def func_delta_der1(self):
        # NOTE: 1 or multiple functions based on derivate order??
        pass

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
            return sorted([self.c * self.mu_ / self.lambda_,
                           1.0])
        elif derivate_order == 1:
            # NOTE : the second element is POSITIV, its (-1)* cannot be the extected value of T_c
            return sorted([1 / (self.lambda_ - self.c * self.mu_),
                           self.c * self.mu_ / (self.lambda_ * self.c * self.mu_ - (self.lambda_ ** 2))])
        elif derivate_order == 2:
            # NOTE: the 4th element is Negative, it cannot be the second moment of T_c
            return sorted([2 * self.c * self.mu_ / ((self.c * self.mu_ - self.lambda_) ** 3),
                           2 * ((self.c * self.mu_) ** 2) / self.lambda_ / ((self.c * self.mu_ - self.lambda_) ** 3),
                           2 * self.lambda_ / ((self.lambda_ - self.c * self.mu_) ** 2),
                           -2 * self.c * self.mu_ * self.lambda_ / ((self.c * self.mu_ - self.lambda_) ** 2)])


if __name__ == '__main__':
    analyzer = MMc_WeightedBusyTimeAnalyzer(lambda_=2, mu_=3, c=3, n1=1, n2=1, nc=1)
    res = analyzer.func_delta_der0(k=2, s=0)
    print len(res)
    print res