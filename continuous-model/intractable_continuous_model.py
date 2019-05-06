import itertools
import sys
import continuous_model
import math

sys.setrecursionlimit(100000)


class MMcWeightedBusyTimeAnalyzer(continuous_model.MMcAnalyzer):

    def __init__(self, lambda_, mu_, c, solution_pair_index=None, n1=1, n2=1, nc=10, nk=10):
        """
        Models an M/M/c queue.

        :param lambda_:
        :param mu_:
        :param c:
        """
        super(MMcWeightedBusyTimeAnalyzer, self).__init__(lambda_, mu_, c, solution_pair_index)
        self.n2 = n2
        self.n1 = n1
        self.nc = nc
        self.nk = nk
        # keyed by 4-tuples of (k, current_n1, current_n2, current_nc)
        self.cache = {}

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

    def func_delta_der0(self, k, s, current_n1=None, current_n2=None, current_nc=None, current_nk=None):
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
        if current_nk is None:
            current_nk = self.nk
        if k < 1 or k > self.c:
            raise ValueError("k must be between 1 and c")
        final_solution_list = []
        cache_key = (0, k, current_n1, current_n2, current_nc, current_nk)
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
                    possible_solutions_prev_rec = self.func_delta_der0(1, s, current_n1 - 1, self.n2, current_nc, current_nk)
                    for delta_value in possible_solutions_prev_rec:
                         final_solution_list.append( self.func_upsilon(1, s) * (self.p_dep(1) * delta_value + self.p_arr(1)) )
                    final_solution_list = set(final_solution_list)
                    self.set_cache(cache_key, final_solution_list)
                    return final_solution_list
            else:
                if current_n1 == 0:
                    # we have reached the bottom (k==1), but we still need to consider some more 1 --> 2 transitions for this last 0 -->
                    # 1 transition.
                    possible_solutions_prev_rec = self.func_delta_der0(2, s, 0, current_n2 - 1, current_nc, current_nk)
                    for delta_value in possible_solutions_prev_rec:
                        final_solution_list.append( self.func_upsilon(1, s) * (self.p_dep(1) + self.p_arr(1) * delta_value) )
                    final_solution_list = set(final_solution_list)
                    self.set_cache(cache_key, final_solution_list)
                    return final_solution_list
                else:
                    # we have reached the bottom (k==1), but we still need to consider some more 1 --> 2 transitions and some more 0 -->
                    # 1 transitions.
                    # so we decrease the desired number of 1 --> 2 transitions.
                    possible_solutions_prev_rec_1_2 = self.func_delta_der0(2, s, current_n1, current_n2 - 1, current_nc, current_nk)
                    # so we decrease the desired number of 0 --> 1 transitions.
                    possible_solutions_prev_rec_0_1 = self.func_delta_der0(1, s, current_n1 - 1, current_n2, current_nc, current_nk)
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
                possible_solutions_prev_rec = self.func_delta_der0(self.c - 1, s, current_n1, current_n2, current_nc - 1, current_nk)
            for etha_c_value, delta_value in itertools.product(etha_c_values, possible_solutions_prev_rec):
                final_solution_list.append(etha_c_value * delta_value / float(self.c))
            final_solution_list = set(final_solution_list)
            self.set_cache(cache_key, final_solution_list)
            return final_solution_list
        else:
            # else: 1 < k < c
            if current_nk == 0:
                possible_solutions_dep = [1]
                possible_solutions_arr = [1]
            else:
                possible_solutions_dep = self.func_delta_der0(k - 1, s, current_n1, current_n2, current_nc, current_nk - 1)
                possible_solutions_arr = self.func_delta_der0(k + 1, s, current_n1, current_n2, current_nc, current_nk - 1)
            for delta_arr, delta_dep in itertools.product(possible_solutions_arr, possible_solutions_dep):
                final_solution_list.append(self.func_upsilon(k, k * s) / float(k) * (self.p_dep(k) * delta_dep + self.p_arr(k) * delta_arr))
            final_solution_list = set(final_solution_list)
            self.set_cache(cache_key, final_solution_list)
            return final_solution_list

    def func_delta_der1(self, k, s, current_n1=None, current_n2=None, current_nc=None, current_nk=None):
        """

        :param k:
        :param s:
        :param current_n1:
        :param current_n2:
        :param current_nc:
        :param current_nk:
        :return:
        """
        if current_n1 is None:
            current_n1 = self.n1
        if current_n2 is None:
            current_n2 = self.n2
        if current_nc is None:
            current_nc = self.nc
        if current_nk is None:
            current_nk = self.nk
        if k < 1 or k > self.c:
            raise ValueError("k must be between 1 and c")
        final_solution_list = []
        # first element of cache key is the derivate order.
        cache_key = (1, k, current_n1, current_n2, current_nc, current_nk)
        cache = self.get_cache(cache_key)
        if cache is not None:
            return cache
        if k == 1:
            if current_n2 == 0:
                if current_n1 == 0:
                    # self.func_upsilon(k, s, derivate_order=1) * (self.p_dep(k) + self.p_arr(k)), but the second == 1 always
                    final_solution_list = [self.func_upsilon(1, s, derivate_order=1)]
                    self.set_cache(cache_key, final_solution_list)
                    return final_solution_list
                else:
                    possible_solutions_der0 = self.func_delta_der0(1, s, current_n1 - 1, self.n2, current_nc, current_nk)
                    possible_solutions_der1 = self.func_delta_der1(1, s, current_n1 - 1, self.n2, current_nc, current_nk)
                    upsilon_der1 = self.func_upsilon(1, s, derivate_order=1)
                    for delta_der1_value, delta_der0_value in itertools.product(possible_solutions_der1,
                                                                                possible_solutions_der0):
                        final_solution_list.append( self.p_dep(1) * (upsilon_der1 * delta_der0_value  +
                                                                     self.func_upsilon(1, s) * delta_der1_value) +
                                                    self.p_arr(1) * upsilon_der1)
                    final_solution_list = set(final_solution_list)
                    self.set_cache(cache_key, final_solution_list)
                    return final_solution_list
            else:
                if current_n1 == 0:
                    possible_solutions_der0 = self.func_delta_der0(2, s, 0, current_n2 - 1, current_nc, current_nk)
                    possible_solutions_der1 = self.func_delta_der1(2, s, 0, current_n2 - 1, current_nc, current_nk)
                    upsilon_der1 = self.func_upsilon(1, s, derivate_order=1)
                    for delta_der1_value, delta_der0_value in itertools.product(possible_solutions_der1,
                                                                                possible_solutions_der0):
                        final_solution_list.append( self.p_dep(1) * upsilon_der1 +
                                                    self.p_arr(1) * (upsilon_der1 * delta_der0_value +
                                                                     self.func_upsilon(1, s) * delta_der1_value) )
                    final_solution_list = set(final_solution_list)
                    self.set_cache(cache_key, final_solution_list)
                    return final_solution_list
                else:
                    # we have reached the bottom (k==1), but we still need to consider some more 1 --> 2 transitions and some more 0 -->
                    # 1 transitions. For both the derivate and the 0th derivate
                    # so we decrease the desired number of 1 --> 2 transitions. For both the derivate and the 0th derivate
                    possible_solutions_prev_rec_1_2_der0 = self.func_delta_der0(2, s, current_n1, current_n2 - 1, current_nc, current_nk)
                    possible_solutions_prev_rec_1_2_der1 = self.func_delta_der1(2, s, current_n1, current_n2 - 1, current_nc, current_nk)
                    # so we decrease the desired number of 0 --> 1 transitions. For both the derivate and the 0th derivate
                    possible_solutions_prev_rec_0_1_der0 = self.func_delta_der0(1, s, current_n1 - 1, current_n2, current_nc, current_nk)
                    possible_solutions_prev_rec_0_1_der1 = self.func_delta_der1(1, s, current_n1 - 1, current_n2, current_nc, current_nk)
                    upsilon_der0 = self.func_upsilon(1, s)
                    upsilon_der1 = self.func_upsilon(1, s, derivate_order=1)
                    for delta_0_1_der1, delta_1_2_der1, delta_0_1_der0, delta_1_2_der0 in \
                            itertools.product(possible_solutions_prev_rec_0_1_der1,
                                              possible_solutions_prev_rec_1_2_der1,
                                              possible_solutions_prev_rec_0_1_der0,
                                              possible_solutions_prev_rec_1_2_der0):
                        final_solution_list.append(self.p_dep(1) * (upsilon_der1 * delta_0_1_der0 + upsilon_der0 * delta_0_1_der1) +
                                                   self.p_arr(1) * (upsilon_der1 * delta_1_2_der0 + upsilon_der0 * delta_1_2_der1))
                    final_solution_list = set(final_solution_list)
                    self.set_cache(cache_key, final_solution_list)
                    return final_solution_list
        if k == self.c:
            etha_c_der0_values = self.func_etha_c(self.c * s)
            etha_c_der1_values = self.func_etha_c(self.c * s, derivate_order=1)
            if current_nc == 0:
                final_solution_list = set(etha_c_der1_values)
                self.set_cache(cache_key, final_solution_list)
                return final_solution_list
            else:
                # Multiple values might come from evaluating the delta
                # we didn't reach bottom, n1, n2 stays the same.
                possible_solutions_prev_rec_der0 = self.func_delta_der0(self.c - 1, s, current_n1, current_n2, current_nc - 1, current_nk)
                possible_solutions_prev_rec_der1 = self.func_delta_der0(self.c - 1, s, current_n1, current_n2, current_nc - 1, current_nk)
            for etha_c_der1_value, delta_der1_value, etha_c_der0_value, delta_der0_value in \
                    itertools.product(etha_c_der1_values,
                                      possible_solutions_prev_rec_der1,
                                      etha_c_der0_values,
                                      possible_solutions_prev_rec_der0):
                final_solution_list.append(etha_c_der1_value * delta_der0_value +
                                           etha_c_der0_value * delta_der1_value / float(self.c))
            final_solution_list = set(final_solution_list)
            self.set_cache(cache_key, final_solution_list)
            return final_solution_list
        else:
            # else: 1 < k < c
            upsilon_der0 = self.func_upsilon(k, k * s)
            upsilon_der1 = self.func_upsilon(k, k * s, derivate_order=1)
            if current_nk == 0:
                # this is the deriavet if we ould disregard the dependency on the one higher and one lower recursions.
                final_solution_list = [upsilon_der1]
                self.set_cache(cache_key, set(final_solution_list))
                return final_solution_list
            else:
                possible_solutions_dep_der0 = self.func_delta_der0(k - 1, s, current_n1, current_n2, current_nc, current_nk - 1)
                possible_solutions_dep_der1 = self.func_delta_der1(k - 1, s, current_n1, current_n2, current_nc, current_nk - 1)
                possible_solutions_arr_der0 = self.func_delta_der0(k + 1, s, current_n1, current_n2, current_nc, current_nk - 1)
                possible_solutions_arr_der1 = self.func_delta_der1(k + 1, s, current_n1, current_n2, current_nc, current_nk - 1)
            for delta_arr_der0, delta_dep_der0, delta_arr_der1, delta_dep_der1 in \
                    itertools.product(possible_solutions_arr_der0,
                                      possible_solutions_dep_der0,
                                      possible_solutions_arr_der1,
                                      possible_solutions_dep_der1):
                final_solution_list.append(self.p_dep(k) * (upsilon_der1 * delta_dep_der0 +
                                                            upsilon_der0 * delta_dep_der1 / float(k)) +
                                           self.p_arr(k) * (upsilon_der1 * delta_arr_der0 +
                                                            upsilon_der0 * delta_arr_der1 / float(k)))
            final_solution_list = set(final_solution_list)
            self.set_cache(cache_key, final_solution_list)
            return final_solution_list


if __name__ == '__main__':
    analyzer = MMcWeightedBusyTimeAnalyzer(lambda_=25, mu_=1, c=30, n1=10, n2=1, nc=1, nk=1, solution_pair_index=0)
    k = 28
    print "Expected value of T_c: %s" % map(lambda x: -1.0*x, analyzer.func_etha_c(s=0, derivate_order=1))
    print "Standard deviation of T_c: %s" % map(math.sqrt, analyzer.func_etha_c(s=0, derivate_order=2))
    print "Expected value of a the weighted busy time: %s" % map(lambda x: -1.0*x, analyzer.func_delta_der1(k=k, s=0))
