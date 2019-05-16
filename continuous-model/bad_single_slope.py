import math
import itertools
import continuous_model


class SingleSlopeWeightedBusyTimeMMcAnalyer(continuous_model.MMcAnalyzer):

    def __init__(self, lambda_, mu_, c, solution_pair_index=0):
        """
        Models the weighted busy time only until the first occurance of an empty/non-busy (k=0) system state.
        The predictions are the best, when the server is loaded, k is big and the time intervals for checking the average CPU utilization
        is short.

        :param lambda_:
        :param mu_:
        :param c:
        """
        super(SingleSlopeWeightedBusyTimeMMcAnalyer, self).__init__(lambda_, mu_, c, solution_pair_index)

    def func_delta_der0(self, k, s):
        """
        LST of the area of a single slope while reducing the active servers from k to k-1.

        :param k:
        :param s:
        :return:
        """
        if k == self.c:
            etha_c_values = self.func_etha_c(s, derivate_order=0)
            return etha_c_values
        elif 1 <= k < self.c:
            etha_k_values = self.func_etha(k, s)
            delta_k_plus_1_values = self.func_delta_der0(k + 1, s)
            possible_results = []
            # solution index is handled inside etha c and etha k
            for etha_k, delta_k_plus_1 in itertools.product(etha_k_values, delta_k_plus_1_values):
                possible_results.append(self.p_dep(k) * self.func_upsilon(k, s) +
                                        self.p_arr(k) * etha_k * delta_k_plus_1)
            return possible_results
        else:
            raise ValueError("k must be between 1 and c")

    def func_delta_der1(self, k, s):
        """
        First derivate of LST of the area of a single slope while reducing the active servers from k to k-1.

        :param k:
        :param s:
        :return:
        """
        if k == self.c:
            etha_c_values = self.func_etha_c(s, derivate_order=1)
            return etha_c_values
        elif 1 <= k < self.c:
            possible_results = []
            delta_k_plus_1_values = self.func_delta_der0(k + 1, s)
            delta_k_plus_1_values_der1 = self.func_delta_der1(k + 1, s)
            etha_k_values = self.func_etha(k, s)
            etha_k_values_der1 = self.func_etha(k, s, derivate_order=1)
            # all values are single element lists if the solution index is used.
            for delta, delta_der1, etha, etha_der1 in itertools.product(delta_k_plus_1_values, delta_k_plus_1_values_der1,
                                                                        etha_k_values, etha_k_values_der1):
                possible_results.append(self.p_dep(k) * self.func_upsilon(k, s, derivate_order=1) +
                                        self.p_arr(k) * (etha_der1 * delta + delta_der1 * etha))
            return possible_results
        else:
            raise ValueError("k must be between 1 and c")

    def func_delta_der2(self, k, s):
        """
        Second derivate of LST of the area of a single slope while reducing the active servers from k to k-1.

        :param k:
        :param s:
        :return:
        """
        if k == self.c:
            etha_c_values = self.func_etha_c(s, derivate_order=2)
            return etha_c_values
        elif 1 <= k < self.c:
            possible_results = []
            delta_k_plus_1_values = self.func_delta_der0(k + 1, s)
            delta_k_plus_1_values_der1 = self.func_delta_der1(k + 1, s)
            delta_k_plus_1_values_der2 = self.func_delta_der2(k + 1, s)
            etha_k_values = self.func_etha(k, s)
            etha_k_values_der1 = self.func_etha(k, s, derivate_order=1)
            etha_k_values_der2 = self.func_etha(k, s, derivate_order=2)
            # all values are single element lists if the solution index is used.
            for delta, delta_der1, delta_der2, etha, etha_der1, etha_der2 in itertools.product(delta_k_plus_1_values,
                                                                                               delta_k_plus_1_values_der1,
                                                                                               delta_k_plus_1_values_der2,
                                                                                               etha_k_values,
                                                                                               etha_k_values_der1,
                                                                                               etha_k_values_der2):
                possible_results.append(self.p_dep(k) * self.func_upsilon(k, s, derivate_order=2) +
                                        self.p_arr(k) * (etha_der2 * delta + 2.0 * etha_der1 * delta_der1 + delta_der2 * etha))
            return possible_results
        else:
            raise ValueError("k must be between 1 and c")

    def func_delta_total_der0(self, k, s):
        """
        LST of the total area under a single slope while reducing the active servers from k to k-1.

        :param k:
        :param s:
        :return:
        """
        possible_results = []
        if k == self.c:
            etha_c_values = self.func_etha_c(self.c * s, derivate_order=0)
            for etha in etha_c_values:
                possible_results.append(etha / float(self.c))
            return possible_results
        elif 1 <= k < self.c:
            etha_ks_values = self.func_etha(k, k * s)
            delta_k_plus_1_values = self.func_delta_der0(k + 1, s)
            for etha_ks, delta_k_plus_1 in itertools.product(etha_ks_values, delta_k_plus_1_values):
                possible_results.append(self.p_dep(k) * self.func_upsilon(k, k * s) / float(k) +
                                        self.p_arr(k) * etha_ks / float(k) * delta_k_plus_1)
            return possible_results
        else:
            raise ValueError("k must be between 1 and c")


if __name__ == '__main__':
    analyzer = SingleSlopeWeightedBusyTimeMMcAnalyer(lambda_=20, mu_=1, c=30, solution_pair_index=0)
    k = 30
    print "Expected value of T_%s: %s" % (k, map(lambda x: -1.0*x, analyzer.func_etha(k=k, s=0, derivate_order=1)))
    print "Standard deviation of T_%s: %s" % (k, map(math.sqrt, analyzer.func_etha(k=k, s=0, derivate_order=2)))
    print "Expected value of a slope: %s" % map(lambda x: -1.0*x, analyzer.func_delta_der1(k=k, s=0))
    print "Standard deviation of a slope: %s" % map(math.sqrt, analyzer.func_delta_der2(k=k, s=0))
